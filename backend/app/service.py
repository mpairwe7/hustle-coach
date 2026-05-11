"""CoachingService — orchestrates the full HustleScale pipeline.

The National Youth Micro-Enterprise Accelerator. Pipeline:
1. Input guardrails (injection, blocked content)
2. Semantic cache lookup
3. Domain classification (supervisor)
4. Market intelligence (if market_prices domain)
5. Hybrid RAG retrieval
6. LLM synthesis with agentic tool calling (8 tools)
7. Business plan extraction (if business_plan domain)
8. Output guardrails (hype detection, PII, grounding)
9. Cache store
"""

from __future__ import annotations

import json as _json
import logging
import os
import time
import threading
import uuid
from collections import deque

from .agents.supervisor import classify
from .business_plan import extract_business_plan, build_plan_prompt_supplement
from .cache import SemanticCache
from .guardrails import InputGuard, OutputGuard, scan_retrieved_text, passage_marker
from .llm import CoachLLM
from .market_intel import MarketIntelligence
from .models import ChatResponse, Citation, ToolCall
from .retriever import HybridRetriever, compute_faithfulness, build_citations

logger = logging.getLogger(__name__)

# ─── Stop-word set for keyword filtering ───
_STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "because", "but", "and", "or", "if", "while", "about", "up",
    "it", "its", "this", "that", "these", "those", "i", "me", "my",
    "we", "our", "you", "your", "he", "him", "his", "she", "her",
    "they", "them", "their", "what", "which", "who", "whom",
    "am", "also", "any", "many", "much", "get", "got", "like",
    "please", "help", "tell", "know", "want", "think", "make",
})


def _filter_stop_words(text: str) -> list[str]:
    """Tokenize text and remove stop words, returning meaningful keywords."""
    tokens = text.lower().split()
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


# Session store with TTL
SESSION_TTL = 86400  # 24 hours
MAX_SESSIONS = 5000


def _get_redis():
    """Optional Redis connection for session persistence."""
    url = os.getenv("REDIS_URL")
    if not url:
        return None
    try:
        import redis
        return redis.Redis.from_url(url, decode_responses=True, socket_timeout=2)
    except Exception:
        return None


def _generate_follow_ups(query: str, domain: str, answer: str, locale: str = "en") -> list[str]:
    """Generate 2-3 contextual follow-up suggestions based on domain, answer, and locale."""
    q = query.lower()

    # ── Locale-specific follow-up maps ──
    _follow_maps: dict[str, dict[str, list[str]]] = {
        "en": {
            "business_plan": [
                "What are the biggest risks of this business?",
                "How should I market this to my first customers?",
                "What licenses or permits do I need?",
                "How do I keep financial records for this business?",
                "What funding or grants can I apply for?",
                "What if I have less capital — can I start smaller?",
            ],
            "finance": [
                "How do I separate business money from personal money?",
                "What is a VSLA and how do I join one?",
                "How do I price my products for profit?",
                "When should I consider taking a loan?",
                "How do I track my daily expenses?",
            ],
            "marketing": [
                "Write me a WhatsApp marketing message I can send today",
                "How do I get my first 10 customers?",
                "What free marketing channels work best in Kampala?",
                "How do I build repeat customers?",
                "Should I use Facebook or WhatsApp for my business?",
            ],
            "risk": [
                "How can I reduce these risks before I start?",
                "What insurance options exist for small businesses?",
                "Should I start smaller to test the market first?",
                "What happens if my business fails — how do I recover?",
                "How do I build an emergency fund?",
            ],
            "market_prices": [
                "Where can I buy these items at the cheapest price?",
                "How do prices change with seasons?",
                "Can you help me make a budget using these prices?",
                "What other items do I need for this business?",
            ],
            "success_stories": [
                "How can I apply their strategy to my business?",
                "What mistakes should I avoid based on their experience?",
                "Help me create a similar business plan",
                "What other success stories do you have?",
            ],
            "funding": [
                "How do I apply for government youth funds like YLP?",
                "What is the difference between a grant and a loan?",
                "Can I get funding without collateral?",
                "How do I start a VSLA in my community?",
                "What happens if my funding application is rejected?",
            ],
            "cooperative": [
                "How many people do I need to form a group?",
                "What is the difference between a SACCO and a VSLA?",
                "How do we handle profit sharing fairly?",
                "How do I protect myself in a group business?",
                "Can our cooperative apply for Emyooga funding?",
            ],
        },
        "lg": {
            "business_plan": [
                "Bizinensi eno erina obulabe ki obukulu?",
                "Nkola ntya okutunda eri bakasitoma bange abaasooka?",
                "Njagala layisensi oba palimenti ki?",
                "Nkuuma ntya ebyenfuna by'omulimu guno?",
                "Nsobola okufuna ssente ki okuva mu gavumenti?",
                "Bwe mba nina ssente ntono — nsobola okutandika ku bunene obutono?",
            ],
            "finance": [
                "Njawula ntya ssente z'omulimu n'ez'obuntu?",
                "VSLA ky'ekiki era ngyingiramu ntya?",
                "Nteeka ntya emiwendo okufuna amagoba?",
                "Ntwalira ddi okusaba looni?",
                "Ngoberera ntya ebintu bye nsaasaanya buli lunaku?",
            ],
            "marketing": [
                "Mpandiikira obubaka bwa WhatsApp bwe nsobola okusindika leero",
                "Nfuna ntya bakasitoma bange 10 abaasooka?",
                "Mikutu ki gy'okutunda egikola obulungi mu Kampala?",
                "Nkola ntya bakasitoma abakomawo?",
                "Nkozese Facebook oba WhatsApp ku bizinensi yange?",
            ],
            "risk": [
                "Nkendeeza ntya ku bulabe buno nga sinnaba kutandika?",
                "Inshulansi ki esobola okukozesebwa ku bizinensi entono?",
                "Ntandike ku bunene obutono okugezesa akatale?",
                "Kiki ekibaawo bizinensi yange bw'egwa — nziramu ntya?",
                "Nkola ntya essente z'obuyambi bw'amangu?",
            ],
            "market_prices": [
                "Nsobola okugula ebintu bino wano ku miwendo emitono?",
                "Emiwendo gyikyuka ntya ng'ebiseera by'omwaka?",
                "Nyamba okukola bajeti n'emiwendo gino",
                "Bintu ki ebirala bye njagala ku bizinensi eno?",
            ],
            "success_stories": [
                "Nsobola ntya okukozesa enteekateeka yaabwe ku bizinensi yange?",
                "Nkendeeza ntya ku nsobi ezikozeddwa?",
                "Nkole enteekateeka y'omulimu ekifaanana?",
                "Olina emboozi endala ez'obuwanguzi?",
            ],
            "funding": [
                "Nsaba ntya ssente z'abavubuka okuva mu gavumenti nga YLP?",
                "Kiki ekikyawulawo wakati w'ekirabo n'ebbanja?",
                "Nsobola okufuna ssente awatali kollatero?",
                "Ntandika ntya VSLA mu kitundu kyange?",
                "Kiki ekibaawo okusaba kwange bw'okugaanibwa?",
            ],
            "cooperative": [
                "Njagala bantu bameka okukola ekibinja?",
                "Kiki ekikyawulawo wakati wa SACCO ne VSLA?",
                "Tugabana ntya amagoba mu bwenkanya?",
                "Neekuuma ntya mu bizinensi ky'ekibinja?",
                "Ekibinja kyaffe kisobola okusaba ssente za Emyooga?",
            ],
        },
        "sw": {
            "business_plan": [
                "Hatari kubwa za biashara hii ni zipi?",
                "Nipasarishe vipi kwa wateja wangu wa kwanza?",
                "Ninahitaji leseni au vibali gani?",
                "Niweke vipi kumbukumbu za fedha?",
                "Ruzuku au mikopo gani ninaweza kuomba?",
                "Nikiwa na mtaji mdogo — naweza kuanza kidogo?",
            ],
            "finance": [
                "Nitenganishe vipi pesa za biashara na za binafsi?",
                "VSLA ni nini na nijiunge vipi?",
                "Niweke bei vipi ili nipate faida?",
                "Ni lini niombe mkopo?",
                "Nifuatilie vipi matumizi yangu ya kila siku?",
            ],
            "marketing": [
                "Niandike ujumbe wa WhatsApp wa kutuma leo",
                "Nipate vipi wateja wangu 10 wa kwanza?",
                "Njia gani bure za masoko zinafanya kazi Kampala?",
                "Niunde vipi wateja wa kurudia?",
                "Nitumie Facebook au WhatsApp kwa biashara yangu?",
            ],
            "risk": [
                "Nipunguze vipi hatari hizi kabla ya kuanza?",
                "Bima gani zinapatikana kwa biashara ndogo?",
                "Nianze kidogo kujaribu soko kwanza?",
                "Nini kinatokea biashara yangu ikishindwa?",
                "Niunde vipi mfuko wa dharura?",
            ],
            "market_prices": [
                "Ninaweza kununua vitu hivi wapi kwa bei nafuu?",
                "Bei zinabadilika vipi na msimu?",
                "Nisaidie kutengeneza bajeti na bei hizi",
                "Vitu gani vingine ninahitaji kwa biashara hii?",
            ],
            "success_stories": [
                "Ninaweza kutumia mkakati wao vipi kwa biashara yangu?",
                "Makosa gani niepuke kutokana na uzoefu wao?",
                "Nisaidie kuunda mpango sawa wa biashara",
                "Una hadithi nyingine za mafanikio?",
            ],
            "funding": [
                "Niombe vipi fedha za vijana kutoka serikali kama YLP?",
                "Kuna tofauti gani kati ya ruzuku na mkopo?",
                "Naweza kupata fedha bila dhamana?",
                "Nianzishe vipi VSLA katika jamii yangu?",
                "Nini kitatokea ombi langu likikataliwa?",
            ],
            "cooperative": [
                "Ninahitaji watu wangapi kuunda kikundi?",
                "Kuna tofauti gani kati ya SACCO na VSLA?",
                "Tunashiriki vipi faida kwa usawa?",
                "Nijilinde vipi katika biashara ya kikundi?",
                "Kikundi chetu kinaweza kuomba fedha za Emyooga?",
            ],
        },
        "nyn": {
            "business_plan": [
                "Obuzibu obukuru bw'omulimu guno ni buki?",
                "Nkora nta okutunda eri abaguzi bange abaasooka?",
                "Njagala layisensi oba palimenti ki?",
                "Nkuuma nta ebyenfuna by'omulimu guno?",
                "Ninsobora okushaba sente ki okuva mu gavumenti?",
                "Nimbika nta ndina sente ntono?",
            ],
            "finance": [
                "Njawura nta sente z'omulimu n'ezo obuntu?",
                "VSLA ni ki era ngyingiramu nta?",
                "Nteeka nta emibazi okutunga amagoba?",
                "Ntwarira ri okushaba looni?",
                "Nigoberera nta ebintu bye ndiisaanya buri rizooba?",
            ],
            "marketing": [
                "Mpandiikira obubaka bwa WhatsApp bwe ninsobora okusindika rero",
                "Ntunga nta abaguzi bange 10 abaasooka?",
                "Nzira ki ey'okutunda erikora obulungi mu Kampala?",
                "Nkora nta abaguzi abagaruka?",
                "Nkozese Facebook oba WhatsApp ku mulimu gwange?",
            ],
            "risk": [
                "Nkendeeza nta obuzibu buno nga tindaatandika?",
                "Inshulansi ki ensobora okukozesebwa ku mulimu gumutono?",
                "Ntandike ku bunene obutono okugezesa akatare?",
                "Niki ekibaho omulimu gwange bw'ogwa?",
                "Nkora nta sente z'obuyambi bw'amangu?",
            ],
            "market_prices": [
                "Ninsobora okugura ebintu bino waha ku mibazi emitono?",
                "Emibazi egyekyusa nta ng'ebisera by'omwaka?",
                "Nyambako okukora bajeti n'emibazi egyo",
                "Bintu ki ebirare bye njagara ku mulimu guno?",
            ],
            "success_stories": [
                "Ninsobora nta okukozesa enteekateeka yaabo ku mulimu gwange?",
                "Nikendeeza nta ku nsobi ezikorekwa?",
                "Nkore enteekateeka y'omulimu efaanana?",
                "Orina emboozi endare ez'obuwanguzi?",
            ],
            "funding": [
                "Nishaba nta sente z'abavubuka okuva mu gavumenti nga YLP?",
                "Niki ekikyawuranyo wakati w'ekirabo n'ebbanja?",
                "Ninsobora okutunga sente ataliho kollatero?",
                "Ntandika nta VSLA mu kitundu kyange?",
                "Niki ekibaho okushaba kwange bw'okugaanibwa?",
            ],
            "cooperative": [
                "Njagara bantu bameka okukora ekibinja?",
                "Niki ekikyawuranyo wakati wa SACCO ne VSLA?",
                "Tugabana nta amagoba mu bwenkanya?",
                "Neekuuma nta mu mulimu gw'ekibinja?",
                "Ekibinja kyaitu kinisobora okushaba sente za Emyooga?",
            ],
        },
    }

    _default_follow_ups: dict[str, list[str]] = {
        "en": [
            "Help me create a business plan",
            "What business can I start with my budget?",
            "Teach me about saving and managing money",
        ],
        "lg": [
            "Nkole enteekateeka y'omulimu",
            "Bizinensi ki gye nsobola okutandika n'essente zange?",
            "Njigirize okukuŋŋaanya n'okukozesa ssente",
        ],
        "sw": [
            "Nisaidie kuunda mpango wa biashara",
            "Biashara gani ninaweza kuanza na bajeti yangu?",
            "Nifundishe kuhusu kuhifadhi na kudhibiti fedha",
        ],
        "nyn": [
            "Nkore enteekateeka y'omulimu",
            "Mulimu ki gwe ninsobora okutandika n'esente zange?",
            "Nyigirize okukuŋŋaanya n'okukozesa sente",
        ],
    }

    follow_map = _follow_maps.get(locale, _follow_maps["en"])
    default = _default_follow_ups.get(locale, _default_follow_ups["en"])

    suggestions = follow_map.get(domain, default)

    # Filter out suggestions too similar to the original query
    filtered = [s for s in suggestions if not any(w in q for w in s.lower().split()[:3])]
    return filtered[:3]


class CoachingService:
    """Main orchestrator for HustleScale — The National Youth Micro-Enterprise Accelerator."""

    def __init__(self):
        self.retriever = HybridRetriever()
        self.llm = CoachLLM()
        self.cache = SemanticCache()
        self.market = MarketIntelligence()
        self.input_guard = InputGuard()
        self.output_guard = OutputGuard()

        self._sessions: dict[str, deque] = {}
        self._session_timestamps: dict[str, float] = {}
        self._session_lock = threading.Lock()

        self._redis = _get_redis()
        if self._redis:
            logger.info("Redis connected for session persistence")

    def initialize(self):
        """Load models, connect services."""
        self.retriever.initialize()
        self.market.load()

        # Share dense model with cache
        if self.retriever._dense_model:
            self.cache.set_model(self.retriever._dense_model)

        logger.info("CoachingService initialized")

    def generate(
        self,
        query: str,
        locale: str = "en",
        session_id: str | None = None,
        domain: str | None = None,
    ) -> ChatResponse:
        """Full pipeline: guard → cache → route → retrieve → generate → guard."""
        start = time.time()

        # 1. Input guardrails
        guard_result = self.input_guard.check(query)
        if not guard_result.passed:
            return ChatResponse(
                answer=guard_result.reason,
                domain="blocked",
                confidence="high",
                locale=locale,
            )

        query = guard_result.sanitized

        # 2. Semantic cache (locale-aware key)
        cache_key = f"[{locale}] {query}"
        cached = self.cache.lookup(cache_key)
        if cached:
            return ChatResponse(
                answer=cached.get("answer", ""),
                citations=[Citation(**c) for c in cached.get("citations", [])],
                faithfulness=cached.get("faithfulness", 0.0),
                domain=cached.get("domain", "general"),
                confidence=cached.get("confidence", "medium"),
                locale=locale,
                cached=True,
            )

        # 3. Domain classification
        if not domain:
            route = classify(query)
            domain = route.domain or "general"

            if route.route == "redirect":
                return ChatResponse(
                    answer="I'm here to help with business ideas and planning! "
                           "Tell me about a business you'd like to start, and "
                           "I'll help you make a plan.",
                    domain="redirect",
                    confidence="high",
                    locale=locale,
                )

            if route.route == "clarify":
                return ChatResponse(
                    answer="I'd love to help! Could you tell me more about your "
                           "business idea? For example:\n"
                           "- What type of business? (poultry, tailoring, salon, etc.)\n"
                           "- How much money do you have to start?\n"
                           "- Where are you located?",
                    domain="clarify",
                    confidence="medium",
                    locale=locale,
                )

        # 4. Market intelligence (supplement context)
        market_context = ""
        if domain in ("market_prices", "business_plan"):
            prices = self.market.search(query=query)
            if prices:
                market_context = self.market.format_for_context(prices)

        # 5. Hybrid RAG retrieval
        passages = self.retriever.search(query, top_k=5, domain=domain)

        # 5b. Corrective RAG: if avg retrieval score is low, expand query and re-retrieve
        if passages:
            avg_score = sum(
                p.get("score_rerank", p.get("score_rrf", 0)) for p in passages
            ) / max(len(passages), 1)
            if avg_score < 0.3:
                try:
                    from .query import expand_abbreviations, correct_spelling
                    expanded = correct_spelling(expand_abbreviations(query))
                    if expanded != query:
                        retry_passages = self.retriever.search(expanded, top_k=5, domain=domain)
                        if retry_passages:
                            retry_avg = sum(
                                p.get("score_rerank", p.get("score_rrf", 0)) for p in retry_passages
                            ) / max(len(retry_passages), 1)
                            if retry_avg > avg_score:
                                passages = retry_passages
                                logger.info("Corrective RAG improved score: %.2f → %.2f", avg_score, retry_avg)
                except Exception as e:
                    logger.debug("Corrective RAG skipped: %s", e)

        # 5c. Keyword blend — boost passages that match stop-word-filtered query tokens
        keywords = _filter_stop_words(query)
        if keywords and passages:
            for p in passages:
                text_lower = (p.get("text") or "").lower()
                hits = sum(1 for kw in keywords if kw in text_lower)
                if hits:
                    bonus = min(hits / max(len(keywords), 1) * 0.15, 0.15)
                    for score_key in ("score_rerank", "score_rrf", "score_keyword"):
                        if score_key in p:
                            p[score_key] = p[score_key] + bonus
                            break
            # Re-sort passages by best available score after boosting
            passages.sort(
                key=lambda p: p.get("score_rerank", p.get("score_rrf", p.get("score_keyword", 0))),
                reverse=True,
            )

        # Scrub injection from retrieved passages
        for p in passages:
            if p.get("text"):
                p["text"] = scan_retrieved_text(p["text"])

        # Check if we should abstain — skip when conversation has history (follow-up context)
        history = self._get_history(session_id)
        has_context = len(history) > 0 or bool(market_context)
        scores = [
            p.get("score_rerank", p.get("score_rrf", p.get("score_keyword", 0)))
            for p in passages
        ]
        if self.output_guard.should_abstain(scores) and not has_context:
            return ChatResponse(
                answer="I don't have specific information about that in my knowledge "
                       "base, but I can still try to help! Could you tell me more "
                       "about what you're looking for? Or try asking about:\n"
                       "- A specific business type (poultry, tailoring, mobile money)\n"
                       "- Market prices for specific goods\n"
                       "- How to save and manage money\n"
                       "- Success stories from other young entrepreneurs",
                domain=domain,
                confidence="low",
                locale=locale,
            )

        # 6. Build passage context with spotlight markers
        passage_dicts = []
        for i, p in enumerate(passages):
            marker = passage_marker(p.get("source", ""), i)
            passage_dicts.append({
                "text": p.get("text", ""),
                "source": p.get("source", "knowledge-base"),
                "marker": marker,
            })

        # Add market context as an additional passage
        if market_context:
            passage_dicts.append({
                "text": market_context,
                "source": "market-intelligence",
            })

        # Add plan supplement for business plan queries
        enriched_query = query
        if domain == "business_plan":
            supplement = build_plan_prompt_supplement(query, market_context)
            enriched_query = f"{query}\n\n{supplement}"


        # 7. LLM generation — use agentic tool calling for complex queries
        use_tools = domain in ("business_plan", "risk", "market_prices", "funding", "cooperative") and self.llm.is_ready
        if use_tools:
            llm_result = self.llm.generate_with_tools(
                query=enriched_query,
                passages=passage_dicts,
                history=history,
                domain=domain,
                locale=locale,
                market_data=self.market.prices,
            )
        else:
            llm_result = self.llm.generate(
                query=enriched_query,
                passages=passage_dicts,
                history=history,
                domain=domain,
                locale=locale,
            )

        answer = llm_result["text"]

        # 8. Output guardrails
        answer = self.output_guard.sanitize(answer)
        answer = self.output_guard.redact_pii(answer)
        answer, leaked = self.output_guard.check_prompt_leakage(answer)
        answer, hype_flagged = self.output_guard.check_hype(answer)

        # Faithfulness scoring
        context_texts = [p.get("text", "") for p in passages if p.get("text")]
        faithfulness = compute_faithfulness(answer, context_texts)

        # Build disclaimer
        disclaimer = self.output_guard.build_disclaimer(faithfulness, hype_flagged, domain)

        # 9. Try to extract structured business plan
        business_plan = None
        if domain == "business_plan":
            business_plan = extract_business_plan(answer)

        # Build citations
        citations = [Citation(**c) for c in build_citations(passages)]

        # Determine confidence
        confidence = "medium"
        if faithfulness >= 0.6:
            confidence = "high"
        elif faithfulness < 0.3:
            confidence = "low"

        # Save to session
        if session_id:
            self._save_turn(session_id, query, answer)

        # Cache the response
        response_dict = {
            "answer": answer,
            "citations": [c.model_dump() for c in citations],
            "faithfulness": faithfulness,
            "domain": domain,
            "confidence": confidence,
        }
        self.cache.store(cache_key, response_dict)

        elapsed = time.time() - start
        logger.info(
            "Generated response: domain=%s faith=%.2f conf=%s time=%.1fs",
            domain, faithfulness, confidence, elapsed,
        )

        # Collect tool calls from agentic pipeline
        tool_calls = []
        if use_tools and llm_result.get("tool_calls"):
            tool_calls = [ToolCall(**tc) for tc in llm_result["tool_calls"]]

        # Generate contextual follow-up suggestions
        follow_ups = _generate_follow_ups(query, domain or "general", answer, locale)

        return ChatResponse(
            answer=answer,
            citations=citations,
            faithfulness=faithfulness,
            domain=domain or "general",
            business_plan=business_plan,
            confidence=confidence,
            locale=locale,
            disclaimer=disclaimer,
            tool_calls=tool_calls,
            follow_ups=follow_ups,
        )

    async def generate_stream(
        self,
        query: str,
        locale: str = "en",
        session_id: str | None = None,
        domain: str | None = None,
    ):
        """Streaming version — yields SSE chunks."""
        try:
            # Input guard
            guard_result = self.input_guard.check(query)
            if not guard_result.passed:
                yield {
                    "token": guard_result.reason,
                    "done": True,
                    "domain": "blocked",
                }
                return

            query = guard_result.sanitized

            # Route
            if not domain:
                route = classify(query)
                domain = route.domain or "general"

            # Retrieve context
            passages = self.retriever.search(query, top_k=5, domain=domain)
            for p in passages:
                if p.get("text"):
                    p["text"] = scan_retrieved_text(p["text"])

            passage_dicts = [
                {"text": p.get("text", ""), "source": p.get("source", "")}
                for p in passages
            ]

            # Market context
            if domain in ("market_prices", "business_plan"):
                prices = self.market.search(query=query)
                if prices:
                    passage_dicts.append({
                        "text": self.market.format_for_context(prices),
                        "source": "market-intelligence",
                    })

            enriched_query = query
            if domain == "business_plan":
                supplement = build_plan_prompt_supplement(query)
                enriched_query = f"{query}\n\n{supplement}"

            history = self._get_history(session_id)

            # For agentic domains, run tool calls first (sync), then stream final text
            use_tools = domain in ("business_plan", "risk", "market_prices", "funding", "cooperative") and self.llm.is_ready
            tool_log = []

            if use_tools:
                # Phase 1: agentic tool-calling (sync) — emit progress events
                tool_result = self.llm.generate_with_tools(
                    query=enriched_query,
                    passages=passage_dicts,
                    history=history,
                    domain=domain,
                    locale=locale,
                    market_data=self.market.prices,
                )
                tool_log = tool_result.get("tool_calls", [])

                # Emit tool progress events so frontend shows reasoning
                for tc in tool_log:
                    tool_labels = {
                        "market_lookup": "Looking up market prices",
                        "validate_budget": "Validating your budget",
                        "calculate_break_even": "Calculating break-even",
                        "check_regulations": "Checking legal requirements",
                        "assess_risk": "Assessing business risks",
                        "find_funding": "Searching funding opportunities",
                        "find_suppliers": "Finding suppliers near you",
                        "suggest_cooperative": "Finding cooperative models",
                    }
                    label = tool_labels.get(tc["tool"], tc["tool"])
                    yield {"tool_progress": label, "tool": tc["tool"], "round": tc["round"], "done": False}

                # Phase 2: stream the final text (already generated by tool loop)
                answer = tool_result.get("text", "")

                # Output guardrails
                answer = self.output_guard.sanitize(answer)
                answer = self.output_guard.redact_pii(answer)
                answer, _ = self.output_guard.check_prompt_leakage(answer)
                answer, hype = self.output_guard.check_hype(answer)

                context_texts = [p.get("text", "") for p in passages]
                faithfulness = compute_faithfulness(answer, context_texts)
                citations = [
                    {k: v for k, v in c.items() if v is not None}
                    for c in build_citations(passages)
                ]

                # Stream the full text in chunks for animated rendering
                chunk_size = 12
                for i in range(0, len(answer), chunk_size):
                    yield {"token": answer[i:i + chunk_size], "done": False}

                # Extract business plan
                bp = None
                if domain == "business_plan":
                    bp = extract_business_plan(answer)

                yield {
                    "token": "",
                    "done": True,
                    "citations": citations,
                    "faithfulness": faithfulness,
                    "domain": domain,
                    "confidence": "high" if faithfulness >= 0.6 else "medium" if faithfulness >= 0.3 else "low",
                    "disclaimer": self.output_guard.build_disclaimer(faithfulness, hype, domain or ""),
                    "tool_calls": tool_log,
                    "business_plan": bp.model_dump() if bp else None,
                    "follow_ups": _generate_follow_ups(query, domain or "general", answer, locale),
                }

                if session_id:
                    self._save_turn(session_id, query, answer)
                return

            # Non-agentic: standard streaming
            full_text = []
            async for chunk in self.llm.generate_stream(
                query=enriched_query,
                passages=passage_dicts,
                history=history,
                domain=domain,
                locale=locale,
            ):
                if chunk.get("done"):
                    answer = "".join(full_text)
                    context_texts = [p.get("text", "") for p in passages]
                    faithfulness = compute_faithfulness(answer, context_texts)
                    citations = [
                        {k: v for k, v in c.items() if v is not None}
                        for c in build_citations(passages)
                    ]
                    _, hype = self.output_guard.check_hype(answer)

                    yield {
                        "token": "",
                        "done": True,
                        "citations": citations,
                        "faithfulness": faithfulness,
                        "domain": domain,
                        "confidence": "high" if faithfulness >= 0.6 else "medium" if faithfulness >= 0.3 else "low",
                        "disclaimer": self.output_guard.build_disclaimer(faithfulness, hype, domain or ""),
                        "follow_ups": _generate_follow_ups(query, domain or "general", answer, locale),
                    }

                    if session_id:
                        self._save_turn(session_id, query, answer)
                else:
                    full_text.append(chunk.get("token", ""))
                    yield chunk
        except Exception as e:
            logger.error("Streaming error: %s", e)
            yield {"token": "", "done": True, "error": "An error occurred. Please try again."}

    def _get_history(self, session_id: str | None) -> list[dict]:
        if not session_id:
            return []
        with self._session_lock:
            if session_id in self._sessions:
                return list(self._sessions[session_id])
        # Try Redis fallback
        if self._redis:
            try:
                data = self._redis.get(f"session:{session_id}")
                if data:
                    history = _json.loads(data)
                    # Restore to in-memory cache
                    with self._session_lock:
                        self._sessions[session_id] = deque(history, maxlen=30)
                    return history
            except Exception:
                pass
        return []

    def _save_turn(self, session_id: str, query: str, answer: str):
        with self._session_lock:
            # Evict old sessions
            now = time.time()
            if len(self._sessions) > MAX_SESSIONS:
                expired = [
                    sid for sid, ts in self._session_timestamps.items()
                    if now - ts > SESSION_TTL
                ]
                for sid in expired:
                    self._sessions.pop(sid, None)
                    self._session_timestamps.pop(sid, None)

            if session_id not in self._sessions:
                self._sessions[session_id] = deque(maxlen=30)
            self._sessions[session_id].append({"role": "user", "content": query})
            self._sessions[session_id].append({"role": "assistant", "content": answer})
            self._session_timestamps[session_id] = now

        # Write-through to Redis (non-fatal)
        if self._redis:
            try:
                key = f"session:{session_id}"
                self._redis.setex(key, SESSION_TTL, _json.dumps(list(self._sessions[session_id])))
            except Exception:
                pass  # Redis failure is non-fatal

    @property
    def health(self) -> dict:
        return {
            "retriever": self.retriever.is_healthy,
            "llm": self.llm.client is not None,
            "market_intel": len(self.market.prices) > 0,
            "cache": self.cache.stats,
            "sessions": len(self._sessions),
        }
