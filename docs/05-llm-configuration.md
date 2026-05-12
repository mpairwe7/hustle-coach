# 5. LLM Configuration — HustleCoach

## Multi-Provider Client (CoachLLM)

| Provider | Model | Use Case |
|----------|-------|----------|
| Groq | `llama-3.3-70b-versatile` | Primary (free, fast) |
| OpenRouter | Various | Fallback multi-model |
| Claude | `claude-sonnet-4-6` | Complex tool calling |

## Tool-Calling LLM

HustleCoach uses **agentic tool calling** — the LLM can invoke 8 tools during response generation:

```python
response = coach_llm.generate_with_tools(
    query=query,
    tools=TOOL_DEFINITIONS,  # 8 tools
    context=retrieved_passages,
    conversation_history=history
)
```

## System Prompt

```
You are HustleCoach, a business advisor for young Ugandan entrepreneurs.
You have access to tools for market research, financial analysis, and planning.
When answering:
1. Use current Uganda market data (April 2026 prices)
2. Reference funding sources (YLP, UWEP, Emyooga, etc.)
3. Give specific UGX figures, not vague advice
4. Consider rural vs urban context
5. Encourage savings culture and cooperative models
```

## Market Intelligence

Real-time market prices from `knowledge-base/market-prices/`:
- 58+ products with regional prices
- Seasonal trends
- Mobile money charges
- Updated April 2026
