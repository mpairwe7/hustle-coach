"use client";

import type { Milestone } from "@/lib/api";

const CATEGORY_LABELS: Record<string, string> = {
  planning: "Planning",
  registration: "Registration",
  launch: "Launch",
  growth: "Growth",
  general: "General",
};

interface MilestoneListProps {
  milestones: Milestone[];
  onToggle: (id: string, completed: boolean) => void;
  recommendations?: string[];
}

export function MilestoneList({
  milestones,
  onToggle,
  recommendations,
}: MilestoneListProps) {
  const milestonesByCategory: Record<string, Milestone[]> = {};
  milestones.forEach((m) => {
    if (!milestonesByCategory[m.category])
      milestonesByCategory[m.category] = [];
    milestonesByCategory[m.category].push(m);
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {Object.entries(milestonesByCategory).map(([cat, items]) => (
        <div key={cat}>
          <h3
            className="text-sm font-bold mb-3 flex items-center gap-2"
            style={{ color: "var(--color-green-dark)" }}
          >
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{ background: "var(--color-green)" }}
            />
            {CATEGORY_LABELS[cat] || cat}
          </h3>
          <div className="space-y-2">
            {items.map((m) => (
              <button
                key={m.id}
                onClick={() => onToggle(m.id, !m.completed)}
                className="w-full card flex items-start gap-3 text-left !p-3 transition-all"
                style={{
                  borderColor: m.completed
                    ? "rgba(45,106,79,0.2)"
                    : undefined,
                  opacity: m.completed ? 0.7 : 1,
                }}
                aria-pressed={m.completed}
              >
                <div
                  className="flex h-8 w-8 sm:h-6 sm:w-6 shrink-0 items-center justify-center rounded-full text-sm font-bold transition-all"
                  style={{
                    background: m.completed
                      ? "var(--color-green)"
                      : "rgba(0,0,0,0.06)",
                    color: m.completed
                      ? "white"
                      : "var(--color-text-muted)",
                  }}
                >
                  {m.completed ? "\u2713" : ""}
                </div>
                <div>
                  <p
                    className="text-sm font-semibold"
                    style={{
                      color: "var(--color-text)",
                      textDecoration: m.completed
                        ? "line-through"
                        : "none",
                    }}
                  >
                    {m.title}
                  </p>
                  <p
                    className="text-xs mt-0.5"
                    style={{ color: "var(--color-text-muted)" }}
                  >
                    {m.description}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      ))}

      {recommendations && recommendations.length > 0 && (
        <div className="card card-gold">
          <h4
            className="text-sm font-bold mb-2"
            style={{ color: "var(--color-gold-dark)" }}
          >
            Recommendations
          </h4>
          {recommendations.map((r, i) => (
            <p
              key={i}
              className="text-sm mb-1"
              style={{ color: "var(--color-text)" }}
            >
              &#x2192; {r}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
