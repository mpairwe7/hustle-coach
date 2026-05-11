"use client";

import { memo } from "react";

interface Props {
  onSelect: (prompt: string) => void;
}

const PROMPTS = [
  {
    icon: "🐔",
    title: "Poultry Farm",
    prompt:
      "I want to start a poultry farm with 100 broiler chickens. I have UGX 1,500,000 to start. Can you help me make a business plan?",
  },
  {
    icon: "✂️",
    title: "Tailoring Shop",
    prompt:
      "I know how to sew and want to start a tailoring business near schools. I have a sewing machine and UGX 500,000. What should I do?",
  },
  {
    icon: "💰",
    title: "Find Funding",
    prompt:
      "What government grants and youth funds can I apply for to start a business? I'm 23 in Kampala with UGX 200,000.",
  },
  {
    icon: "🍳",
    title: "Rolex Vending",
    prompt:
      "I want to start selling rolexes near Makerere University. I have UGX 200,000. Give me a plan with real prices.",
  },
  {
    icon: "🩺",
    title: "Business Check-Up",
    prompt:
      "My salon business earns UGX 800,000/month but I spend UGX 600,000 on costs. How can I improve my profits?",
  },
  {
    icon: "🤝",
    title: "Start a Cooperative",
    prompt:
      "Me and 5 friends want to start a group business. We each have UGX 200,000. What cooperative model should we use?",
  },
  {
    icon: "📱",
    title: "Mobile Money",
    prompt:
      "I want to start a mobile money business near a market. How much money do I need and how much can I earn?",
  },
  {
    icon: "📈",
    title: "Grow My Business",
    prompt:
      "I sell chapati and have 20 regular customers. How do I get to 100 customers and double my income?",
  },
];

export const StarterPrompts = memo(function StarterPrompts({ onSelect }: Props) {
  return (
    <div className="mx-auto max-w-2xl px-4">
      {/* Welcome */}
      <div className="mb-8 text-center">
        <div
          className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl"
          style={{
            background: "linear-gradient(135deg, var(--color-green), var(--color-green-dark))",
            boxShadow: "0 6px 24px rgba(45,106,79,0.2)",
          }}
        >
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3v18M3 12l3-3 3 3M15 12l3-3 3 3M6 9v9a3 3 0 003 3h6a3 3 0 003-3V9" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold" style={{ color: "var(--color-green-dark)" }}>
          What business do you want to scale?
        </h2>
        <p className="mt-2" style={{ color: "var(--color-text-muted)" }}>
          Tell me your idea, find funding, or pick one below to get started
        </p>
      </div>

      {/* Prompt cards */}
      <div className="grid gap-3 sm:grid-cols-2">
        {PROMPTS.map((p) => (
          <button
            key={p.title}
            onClick={() => onSelect(p.prompt)}
            className="card cursor-pointer text-left transition-all hover:border-green-600"
            style={{ borderColor: "var(--color-cream-dark)" }}
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl">{p.icon}</span>
              <div>
                <div className="font-semibold" style={{ color: "var(--color-text)" }}>
                  {p.title}
                </div>
                <div className="mt-0.5 text-sm line-clamp-2" style={{ color: "var(--color-text-muted)" }}>
                  {p.prompt}
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Ethical note */}
      <div className="disclaimer mx-auto mt-8 max-w-lg text-center">
        <p>
          HustleScale gives advice based on local market data, but{" "}
          <strong>no business is guaranteed to succeed</strong>. Always seek
          mentorship from experienced business owners in your community.
        </p>
      </div>
    </div>
  );
});
