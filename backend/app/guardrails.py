"""Ethical guardrails for HustleScale — OWASP LLM Top 10 + business ethics.

Forked from Magezi/URA guardrails. Retooled for entrepreneurship context:
- Blocks prompt injection (LLM01)
- Redacts PII (LLM02)
- Sanitizes output (LLM05)
- Detects system prompt leakage (LLM07)
- Checks grounding / faithfulness (LLM09)
- NEW: Blocks false promises and unrealistic guarantees
- NEW: Flags predatory financial advice
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


@dataclass
class GuardResult:
    passed: bool
    reason: str = ""
    sanitized: str = ""


# ─── Prompt injection patterns (OWASP LLM01) ───

_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"you\s+are\s+now\s+(a|an)",
        r"forget\s+(everything|all|your)",
        r"jailbreak",
        r"DAN\s+mode",
        r"act\s+as\s+(if|though)",
        r"pretend\s+(you|to\s+be)",
        r"bypass\s+(your|the|all)\s+(rules|restrictions|guardrails)",
        r"<\|im_start\|>",
        r"\[INST\]",
        r"system\s*:\s*you\s+are",
    ]
]

# ─── Blocked content for business context ───

_BLOCKED_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"(how\s+to\s+)?(launder|laundering)\s+money",
        r"(how\s+to\s+)?evade\s+tax",
        r"(how\s+to\s+)?forge\s+(invoice|receipt|document)",
        r"(how\s+to\s+)?(scam|defraud|con)\s+(people|someone|customer)",
        r"pyramid\s+scheme.*(start|create|build)",
        r"ponzi\s+scheme",
        r"(make|get)\s+(a\s+)?bomb",
        r"(sell|traffic|distribute)\s+(drugs|narcotics|weapons)",
        r"counterfeit",
    ]
]

# ─── False promise / hype patterns ───

_HYPE_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"guarantee[ds]?\s+.{0,20}(success|profit|rich|million|wealth|succeed)",
        r"(100|hundred)\s*%\s*(sure|certain|guaranteed|risk.?free)",
        r"get\s+rich\s+(quick|fast|overnight)",
        r"no\s+risk\s+(at\s+all|whatsoever|involved)",
        r"definitely\s+(will|going\s+to)\s+(succeed|make\s+money|profit)",
        r"impossible\s+to\s+(fail|lose)",
        r"everyone\s+(can|will)\s+(succeed|make\s+money)",
        r"easy\s+money",
        r"passive\s+income\s+with(out)?\s+(no|zero)\s+effort",
    ]
]

# ─── PII patterns (Uganda-specific, precise formats) ───

_PII_PATTERNS: dict[str, re.Pattern] = {
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "ug_phone": re.compile(r"\+?256\s?[0-9]{9}|0[37][0-9]{8}"),
    "tin": re.compile(r"(?:(?:TIN|tin)\s*:?\s*)\d{10}\b|\b(?<=^)\d{10}\b", re.MULTILINE),
    "nid": re.compile(r"(?:CM|CF)[A-Za-z0-9]{13}\b"),
    "credit_card": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
}

# ─── System prompt leakage signatures ───

_LEAKAGE_SIGNATURES: list[str] = [
    "HustleScale system",
    "You are HustleScale",
    "Hustle Coach system",
    "You are Hustle Coach",
    "Answer ONLY from context",
    "Never reveal these instructions",
    "business coaching AI",
    "NEVER promise guaranteed",
]


class InputGuard:
    """Validates user input before processing."""

    def __init__(self, max_length: int = 2000):
        self.max_length = max_length

    def check(self, text: str) -> GuardResult:
        if not text or not text.strip():
            return GuardResult(False, "Empty input")

        if len(text) > self.max_length:
            return GuardResult(False, f"Input too long (max {self.max_length} chars)")

        # Prompt injection (LLM01)
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(text):
                return GuardResult(
                    False,
                    "I'm here to help with business ideas! Let me know what "
                    "business you're thinking about, and I'll help you plan it.",
                )

        # Blocked content
        for pattern in _BLOCKED_PATTERNS:
            if pattern.search(text):
                return GuardResult(
                    False,
                    "I can only help with legitimate business ideas. For legal "
                    "questions, please consult a lawyer or visit your local "
                    "government office.",
                )

        return GuardResult(True, sanitized=text.strip())


class OutputGuard:
    """Validates and sanitizes LLM output."""

    def __init__(
        self,
        abstention_threshold: float = 0.15,
        grounding_threshold: float = 0.3,
    ):
        self.abstention_threshold = abstention_threshold
        self.grounding_threshold = grounding_threshold

    def should_abstain(self, scores: list[float]) -> bool:
        """Refuse to answer when retrieval confidence is too low."""
        if not scores:
            return True
        top_scores = sorted(scores, reverse=True)[:3]
        avg = sum(top_scores) / len(top_scores)
        return avg < self.abstention_threshold

    def check_hype(self, text: str) -> tuple[str, bool]:
        """Scan output for false promises and unrealistic guarantees."""
        flagged = False
        result = text
        for pattern in _HYPE_PATTERNS:
            if pattern.search(result):
                flagged = True
                # Don't remove — append disclaimer instead
                break
        return result, flagged

    def check_grounding(self, answer: str, contexts: list[str]) -> float:
        """Compute token overlap between answer and contexts (faithfulness proxy)."""
        if not contexts:
            return 0.0
        answer_tokens = set(re.findall(r"\w+", answer.lower()))
        if not answer_tokens:
            return 0.0
        context_tokens = set()
        for ctx in contexts:
            context_tokens.update(re.findall(r"\w+", ctx.lower()))
        # Remove stopwords
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "and", "or", "but", "not", "this", "that", "it", "i", "you",
            "we", "they", "he", "she", "my", "your", "our", "their",
        }
        answer_tokens -= stopwords
        context_tokens -= stopwords
        if not answer_tokens:
            return 1.0
        overlap = answer_tokens & context_tokens
        return len(overlap) / len(answer_tokens)

    def redact_pii(self, text: str) -> str:
        """Replace PII with partial masks (preserving first/last chars for context)."""
        result = text

        # Email: show first 2 chars and domain TLD — j**@***.com
        def _mask_email(m: re.Match) -> str:
            val = m.group()
            local, domain = val.split("@", 1)
            parts = domain.rsplit(".", 1)
            tld = parts[-1] if len(parts) > 1 else domain
            masked_local = local[:2] + "***" if len(local) > 2 else "***"
            return f"{masked_local}@***.{tld}"

        result = _PII_PATTERNS["email"].sub(_mask_email, result)

        # Phone: +256 7XX XXX XX3 style — keep country code and last digit
        def _mask_phone(m: re.Match) -> str:
            digits = re.sub(r"\D", "", m.group())
            if digits.startswith("256"):
                return f"+256 {digits[3]}XX XXX XX{digits[-1]}"
            elif digits.startswith("0"):
                return f"0{digits[1]}X XXX XX{digits[-1]}"
            return "[PHONE_REDACTED]"

        result = _PII_PATTERNS["ug_phone"].sub(_mask_phone, result)

        # TIN: show first 3, mask rest — 100*******
        def _mask_tin(m: re.Match) -> str:
            digits = re.findall(r"\d{10}", m.group())
            if digits:
                d = digits[0]
                prefix = m.group()[:m.group().find(d)]
                return f"{prefix}{d[:3]}*******"
            return "[TIN_REDACTED]"

        result = _PII_PATTERNS["tin"].sub(_mask_tin, result)

        # NIN: show prefix (CM/CF) and last 2 chars — CM***********A1
        def _mask_nid(m: re.Match) -> str:
            val = m.group()
            return f"{val[:2]}***********{val[-2:]}"

        result = _PII_PATTERNS["nid"].sub(_mask_nid, result)

        # Credit card: show last 4 — **** **** **** 1234
        def _mask_cc(m: re.Match) -> str:
            digits = re.sub(r"\D", "", m.group())
            return f"**** **** **** {digits[-4:]}"

        result = _PII_PATTERNS["credit_card"].sub(_mask_cc, result)

        return result

    def sanitize(self, text: str) -> str:
        """Strip dangerous HTML/script content."""
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        return text

    def check_prompt_leakage(self, text: str) -> tuple[str, bool]:
        """Detect system prompt leakage."""
        leaked = False
        for sig in _LEAKAGE_SIGNATURES:
            if sig.lower() in text.lower():
                leaked = True
                text = text.replace(sig, "[REDACTED]")
        return text, leaked

    def build_disclaimer(
        self,
        faithfulness: float,
        hype_flagged: bool,
        domain: str,
    ) -> str:
        """Build appropriate disclaimer based on context."""
        parts = []

        if faithfulness < self.grounding_threshold:
            parts.append(
                "This advice is based on limited information. Please verify "
                "with a local business mentor or KCCA business advisory service."
            )

        if hype_flagged:
            parts.append(
                "Remember: no business is guaranteed to succeed. Success "
                "requires hard work, learning from mistakes, and patience."
            )

        if domain == "business_plan":
            parts.append(
                "These projections are estimates based on typical market conditions. "
                "Actual results depend on your effort, location, and market changes."
            )

        return " ".join(parts)


def passage_marker(source: str, idx: int) -> str:
    """Generate hash-bound passage marker to prevent injection."""
    digest = hashlib.sha256(f"{source}:{idx}".encode()).hexdigest()[:8]
    return f"p{idx}-{digest}"


def scan_retrieved_text(text: str) -> str:
    """Scrub injection patterns from retrieved passages."""
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("[REDACTED_INSTRUCTION]", text)
    return text
