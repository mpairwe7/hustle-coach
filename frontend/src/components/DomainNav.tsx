"use client";

import { memo } from "react";

interface Props {
  onSelect: (prompt: string) => void;
}

const DOMAINS = [
  { id: "business_plan", icon: "📋", label: "Plan", prompt: "Help me create a business plan for " },
  { id: "funding", icon: "💰", label: "Funding", prompt: "What funding or grants can I apply for to start " },
  { id: "market_prices", icon: "💲", label: "Prices", prompt: "What are current market prices for " },
  { id: "marketing", icon: "📢", label: "Market", prompt: "Help me market my " },
  { id: "risk", icon: "🛡️", label: "Risks", prompt: "What are the risks of starting a " },
  { id: "cooperative", icon: "🤝", label: "Co-op", prompt: "How can I form a cooperative for " },
  { id: "finance", icon: "📊", label: "Finance", prompt: "Teach me about " },
  { id: "success_stories", icon: "⭐", label: "Stories", prompt: "Tell me a success story about a young person who started " },
];

export const DomainNav = memo(function DomainNav({ onSelect }: Props) {
  return (
    <div className="flex gap-1.5 overflow-x-auto pb-1" role="navigation" aria-label="Quick topics">
      {DOMAINS.map((d) => (
        <button
          key={d.id}
          onClick={() => onSelect(d.prompt)}
          className="flex shrink-0 items-center gap-1.5 rounded-full px-4 py-2.5 text-sm font-medium transition-all"
          style={{
            background: "var(--color-surface)",
            border: "1px solid var(--color-cream-dark)",
            color: "var(--color-text)",
            minHeight: "44px",
          }}
          title={d.label}
        >
          <span aria-hidden="true">{d.icon}</span>
          <span>{d.label}</span>
        </button>
      ))}
    </div>
  );
});
