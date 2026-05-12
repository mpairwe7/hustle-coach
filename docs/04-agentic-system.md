# 4. Agentic System — HustleCoach

## 8 Agentic Tools

| Tool | Function | Input | Output |
|------|----------|-------|--------|
| `market_prices` | Current Uganda market prices | product, region | price, trend, source |
| `budget_calculator` | Income/expense analysis | income, costs | budget breakdown |
| `break_even` | Break-even analysis | fixed costs, variable, price | break-even units |
| `funding_match` | Match funding sources | business type, amount | eligible programs |
| `business_plan` | Generate business plan | idea, capital | structured plan |
| `competitor_scan` | Competitor analysis | business, location | market gaps |
| `risk_assessment` | Risk analysis | business type | risk matrix |
| `marketing_strategy` | Marketing plan | business, budget | channel recommendations |

## Supervisor (`agents/supervisor.py`)

Domain router classifying queries into:
- `business_plan` — planning, starting, strategy
- `finance` — pricing, budgets, break-even, saving
- `marketing` — customers, promotion, social media
- `risk` — challenges, insurance, competition
- `market_prices` — specific product prices
- `success_stories` — inspiration, case studies
- `funding` — loans, grants, programs

## Tool Calling Flow

```
Query → Supervisor → Domain
    ↓
LLM generates tool calls:
    {"tool": "market_prices", "args": {"product": "eggs", "region": "Kampala"}}
    ↓
Tool executor returns structured data
    ↓
LLM synthesizes final response with tool outputs
```
