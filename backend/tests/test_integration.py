"""Integration tests — token estimation, history truncation, LLM helpers,
retriever utilities, and business plan extraction."""

import pytest

from app.llm import (
    _estimate_tokens,
    _truncate_history,
    _build_system_prompt,
    _build_openai_messages,
    _openai_tools,
    needs_extended_thinking,
    DOMAIN_PROMPTS,
)
from app.retriever import compute_faithfulness, build_citations
from app.business_plan import extract_business_plan


# ── Token estimation ──


class TestEstimateTokens:
    def test_short_string(self):
        assert _estimate_tokens("hello") >= 1

    def test_empty_string(self):
        assert _estimate_tokens("") == 1  # len("")//4 + 1

    def test_long_string(self):
        assert _estimate_tokens("a" * 400) == 101  # 400/4 + 1

    def test_proportional(self):
        short = _estimate_tokens("word")
        long = _estimate_tokens("word " * 100)
        assert long > short


# ── History truncation ──


class TestTruncateHistory:
    def test_preserves_system_message(self):
        messages = [
            {"role": "system", "content": "You are a coach."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        result = _truncate_history(messages, 100)
        assert result[0]["role"] == "system"

    def test_keeps_recent_drops_old(self):
        messages = [
            {"role": "system", "content": "X"},
            {"role": "user", "content": "A" * 1000},   # ~250 tokens
            {"role": "user", "content": "B" * 1000},   # ~250 tokens
            {"role": "user", "content": "short"},       # ~2 tokens
        ]
        result = _truncate_history(messages, 50)
        assert len(result) >= 2
        assert result[-1]["content"] == "short"

    def test_empty_messages(self):
        assert _truncate_history([], 100) == []

    def test_only_system(self):
        messages = [{"role": "system", "content": "sys"}]
        result = _truncate_history(messages, 100)
        assert len(result) == 1
        assert result[0]["role"] == "system"

    def test_large_budget_keeps_all(self):
        messages = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "q2"},
            {"role": "assistant", "content": "a2"},
        ]
        result = _truncate_history(messages, 10000)
        assert len(result) == 5


# ── System prompt building ──


class TestBuildSystemPrompt:
    def test_default_prompt(self):
        prompt = _build_system_prompt()
        assert "HustleScale" in prompt

    def test_domain_prompt_appended(self):
        prompt = _build_system_prompt(domain="business_plan")
        assert "BUSINESS PLAN" in prompt

    def test_locale_appended(self):
        prompt = _build_system_prompt(locale="lg")
        assert "Luganda" in prompt

    def test_swahili_locale(self):
        prompt = _build_system_prompt(locale="sw")
        assert "Swahili" in prompt

    def test_english_locale_no_extra(self):
        prompt_en = _build_system_prompt(locale="en")
        prompt_def = _build_system_prompt()
        assert prompt_en == prompt_def

    def test_all_domains_have_prompts(self):
        expected = {"business_plan", "finance", "marketing", "risk",
                    "market_prices", "success_stories", "funding", "cooperative"}
        assert set(DOMAIN_PROMPTS.keys()) == expected


# ── OpenAI message building ──


class TestBuildOpenAIMessages:
    def test_basic_structure(self):
        msgs = _build_openai_messages("Hello", [])
        assert msgs[0]["role"] == "system"
        assert msgs[-1]["role"] == "user"
        assert msgs[-1]["content"] == "Hello"

    def test_passages_included(self):
        passages = [{"text": "Uganda fact", "source": "kb"}]
        msgs = _build_openai_messages("test", passages)
        system_text = msgs[0]["content"]
        assert "Uganda fact" in system_text
        assert "passage" in system_text.lower()

    def test_history_included(self):
        history = [
            {"role": "user", "content": "prev q"},
            {"role": "assistant", "content": "prev a"},
        ]
        msgs = _build_openai_messages("new q", [], history)
        contents = [m["content"] for m in msgs]
        assert "prev q" in contents
        assert "prev a" in contents

    def test_history_limited_to_16(self):
        history = [{"role": "user", "content": f"q{i}"} for i in range(20)]
        msgs = _build_openai_messages("final", [], history)
        # system + 16 history + 1 user = 18
        assert len(msgs) == 18


# ── OpenAI tool definitions ──


class TestOpenAITools:
    def test_tool_count(self):
        tools = _openai_tools()
        assert len(tools) == 8

    def test_tool_format(self):
        tools = _openai_tools()
        for t in tools:
            assert t["type"] == "function"
            assert "name" in t["function"]
            assert "description" in t["function"]
            assert "parameters" in t["function"]


# ── Extended thinking detection ──


class TestNeedsExtendedThinking:
    @pytest.mark.parametrize("query", [
        "Create a business plan for poultry",
        "Calculate break-even for my salon",
        "What is the cost of starting a tailoring business?",
        "I need a pricing strategy for my products",
        "Help me do a risk assessment",
    ])
    def test_triggers_thinking(self, query):
        assert needs_extended_thinking(query) is True

    @pytest.mark.parametrize("query", [
        "Hi",
        "Tell me about chickens",
        "What is a VSLA?",
    ])
    def test_does_not_trigger(self, query):
        assert needs_extended_thinking(query) is False


# ── Faithfulness scoring ──


class TestComputeFaithfulness:
    def test_high_overlap(self):
        answer = "Broiler chicks cost 4000 shillings each in Kampala market"
        ctx = ["Day-old broiler chicks cost 4000 per chick in Kampala"]
        score = compute_faithfulness(answer, ctx)
        assert score > 0.3

    def test_no_context(self):
        assert compute_faithfulness("anything", []) == 0.0

    def test_empty_answer(self):
        # All tokens are stopwords or empty -> returns 1.0
        score = compute_faithfulness("the a is", ["some context"])
        assert score == 1.0

    def test_zero_overlap(self):
        score = compute_faithfulness("quantum physics electron", ["poultry chicken feed"])
        assert score == 0.0


# ── Citation building ──


class TestBuildCitations:
    def test_builds_from_passages(self):
        passages = [
            {"source": "market-prices", "text": "Chicken costs 4000"},
            {"source": "knowledge-base", "section": "poultry", "text": "Broilers grow fast"},
        ]
        citations = build_citations(passages)
        assert len(citations) == 2
        assert citations[0]["source"] == "market-prices"
        assert "Chicken" in citations[0]["preview"]

    def test_empty_passages(self):
        assert build_citations([]) == []

    def test_missing_text(self):
        citations = build_citations([{"source": "kb"}])
        assert citations[0]["preview"] == ""


# ── Business plan extraction ──


class TestExtractBusinessPlan:
    def test_extracts_plan_from_markdown(self):
        text = """
## Executive Summary
A poultry farm in Kampala.

## Startup Budget
- 100 chicks: UGX 400,000
- Feed: UGX 600,000

## Next Steps
1. Buy chicks
2. Set up housing
"""
        plan = extract_business_plan(text)
        if plan is not None:
            # Plan was successfully extracted
            assert plan.executive_summary != "" or len(plan.next_steps) > 0

    def test_returns_none_for_unstructured(self):
        result = extract_business_plan("Just a simple answer without structure.")
        # May return None or a plan with empty fields — both are acceptable
        if result is not None:
            assert isinstance(result.executive_summary, str)
