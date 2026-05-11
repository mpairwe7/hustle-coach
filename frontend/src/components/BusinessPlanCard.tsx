"use client";

import { memo, useState } from "react";
import type { BusinessPlan } from "@/lib/api";

interface Props { plan: BusinessPlan }
const fmt = (n: number) => `UGX ${n.toLocaleString()}`;

export const BusinessPlanCard = memo(function BusinessPlanCard({ plan }: Props) {
  const [checkedSteps, setCheckedSteps] = useState<Set<number>>(new Set());
  const [expandedRisk, setExpandedRisk] = useState<number | null>(null);

  const toggleStep = (i: number) => {
    setCheckedSteps((prev) => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  };

  const completedCount = checkedSteps.size;
  const totalSteps = plan.next_steps?.length || 0;

  return (
    <div className="space-y-3 animate-fade-in">
      {/* Header */}
      {plan.business_name && (
        <div className="rounded-xl p-4"
          style={{ background: "linear-gradient(135deg, var(--color-green), var(--color-green-dark))", color: "white" }}>
          <h2 className="text-lg font-bold">{plan.business_name}</h2>
          {plan.executive_summary && <p className="mt-1 text-sm opacity-90">{plan.executive_summary}</p>}
          {plan.confidence && (
            <span className="mt-2 inline-block rounded-full px-3 py-0.5 text-[11px] font-semibold"
              style={{ background: "rgba(255,255,255,0.2)" }}>
              Confidence: {plan.confidence}
            </span>
          )}
        </div>
      )}

      {/* Budget Tables Side-by-Side */}
      <div className="grid gap-3 sm:grid-cols-2">
        {plan.startup_budget && plan.startup_budget.length > 0 && (
          <div className="card">
            <h3 className="mb-2 text-sm font-bold flex items-center gap-1.5" style={{ color: "var(--color-green-dark)" }}>
              <span aria-hidden="true">💰</span> Startup Budget
            </h3>
            <div className="space-y-1.5">
              {plan.startup_budget.map((item, i) => (
                <div key={i} className="flex justify-between text-sm">
                  <span className="text-[13px]">{item.item}</span>
                  <span className="font-mono text-[13px] font-medium" style={{ color: "var(--color-green)" }}>{fmt(item.amount_ugx)}</span>
                </div>
              ))}
              <div className="flex justify-between border-t pt-1.5 font-bold text-sm" style={{ borderColor: "var(--color-cream-dark)" }}>
                <span>Total</span>
                <span className="font-mono" style={{ color: "var(--color-green)" }}>{fmt(plan.total_startup_cost || 0)}</span>
              </div>
            </div>
          </div>
        )}

        {plan.monthly_costs && plan.monthly_costs.length > 0 && (
          <div className="card">
            <h3 className="mb-2 text-sm font-bold flex items-center gap-1.5" style={{ color: "var(--color-gold-dark)" }}>
              <span aria-hidden="true">📅</span> Monthly Costs
            </h3>
            <div className="space-y-1.5">
              {plan.monthly_costs.map((item, i) => (
                <div key={i} className="flex justify-between text-sm">
                  <span className="text-[13px]">{item.item}</span>
                  <span className="font-mono text-[13px]">{fmt(item.amount_ugx)}</span>
                </div>
              ))}
              <div className="flex justify-between border-t pt-1.5 font-bold text-sm" style={{ borderColor: "var(--color-cream-dark)" }}>
                <span>Total/month</span>
                <span className="font-mono" style={{ color: "var(--color-gold-dark)" }}>{fmt(plan.total_monthly_cost || 0)}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Revenue + Break-Even Cards */}
      {(plan.revenue_projection || plan.break_even) && (
        <div className="grid gap-3 sm:grid-cols-2">
          {plan.revenue_projection && (
            <div className="card card-gold text-center">
              <p className="text-xs font-semibold mb-1" style={{ color: "var(--color-gold-dark)" }}>Monthly Revenue</p>
              <p className="text-2xl font-bold" style={{ color: "var(--color-green)" }}>{fmt(plan.revenue_projection.monthly_revenue)}</p>
              <p className="text-xs mt-1" style={{ color: "var(--color-text-muted)" }}>
                Profit: <strong style={{ color: "var(--color-green)" }}>{fmt(plan.revenue_projection.monthly_profit)}</strong>/mo
              </p>
            </div>
          )}
          {plan.break_even && (
            <div className="card card-gold text-center">
              <p className="text-xs font-semibold mb-1" style={{ color: "var(--color-gold-dark)" }}>Break-Even</p>
              <p className="text-2xl font-bold" style={{ color: "var(--color-green)" }}>
                {plan.break_even.months} <span className="text-sm font-normal">months</span>
              </p>
              <p className="text-xs mt-1" style={{ color: "var(--color-text-muted)" }}>{plan.break_even.explanation}</p>
            </div>
          )}
        </div>
      )}

      {/* Pricing Strategy */}
      {plan.pricing_strategy && (
        <div className="card">
          <h3 className="mb-2 text-sm font-bold flex items-center gap-1.5" style={{ color: "var(--color-green-dark)" }}>
            <span aria-hidden="true">🏷️</span> Pricing Strategy
          </h3>
          <p className="text-[13px] leading-relaxed" style={{ color: "var(--color-text)" }}>{plan.pricing_strategy}</p>
        </div>
      )}

      {/* Marketing Script — copyable */}
      {plan.marketing_script && (
        <div className="card" style={{ borderColor: "rgba(212,160,23,0.2)" }}>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-bold flex items-center gap-1.5" style={{ color: "var(--color-gold-dark)" }}>
              <span aria-hidden="true">📢</span> Marketing Script
            </h3>
            <button
              onClick={() => navigator.clipboard.writeText(plan.marketing_script || "")}
              className="msg-action-btn text-[11px]" title="Copy to WhatsApp">
              📋 Copy
            </button>
          </div>
          <div className="rounded-lg p-3 text-[13px] leading-relaxed italic"
            style={{ background: "rgba(212,160,23,0.06)", color: "var(--color-text)" }}>
            {plan.marketing_script}
          </div>
        </div>
      )}

      {/* Risk Assessment */}
      {plan.risks && plan.risks.length > 0 && (
        <div className="card">
          <h3 className="mb-2 text-sm font-bold flex items-center gap-1.5" style={{ color: "var(--color-green-dark)" }}>
            <span aria-hidden="true">⚠️</span> Risk Assessment
          </h3>
          <div className="space-y-2">
            {plan.risks.map((risk, i) => (
              <div key={i}
                className="rounded-lg p-2.5 cursor-pointer transition-all"
                style={{ background: expandedRisk === i ? "rgba(45,106,79,0.06)" : "var(--color-cream)" }}
                onClick={() => setExpandedRisk(expandedRisk === i ? null : i)}>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-[13px]">{risk.risk}</span>
                  <div className="flex items-center gap-1.5">
                    <span className={`badge badge-${risk.likelihood === "high" ? "low" : risk.likelihood === "low" ? "high" : "medium"}`}>
                      {risk.likelihood}
                    </span>
                    <span className="text-[10px]" style={{ color: "var(--color-text-light)" }}>
                      {expandedRisk === i ? "▲" : "▼"}
                    </span>
                  </div>
                </div>
                {expandedRisk === i && (
                  <p className="mt-2 text-xs animate-fade leading-relaxed" style={{ color: "var(--color-text-muted)" }}>
                    <strong>Mitigation:</strong> {risk.mitigation}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Next Steps — Checkable */}
      {plan.next_steps && plan.next_steps.length > 0 && (
        <div className="rounded-xl p-4"
          style={{ background: "linear-gradient(135deg, rgba(212,160,23,0.06), rgba(45,106,79,0.04))", border: "1px solid rgba(212,160,23,0.15)" }}>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold flex items-center gap-1.5" style={{ color: "var(--color-green-dark)" }}>
              <span aria-hidden="true">🎯</span> Next Steps — This Week
            </h3>
            <span className="text-[11px] font-semibold" style={{ color: completedCount === totalSteps ? "var(--color-green)" : "var(--color-text-muted)" }}>
              {completedCount}/{totalSteps} done
            </span>
          </div>

          {/* Progress bar */}
          <div className="h-1.5 rounded-full mb-3" style={{ background: "rgba(0,0,0,0.06)" }}>
            <div className="h-full rounded-full transition-all duration-500"
              style={{ width: `${totalSteps ? (completedCount / totalSteps) * 100 : 0}%`, background: "linear-gradient(90deg, var(--color-green), var(--color-gold))" }} />
          </div>

          <ol className="space-y-2">
            {plan.next_steps.map((step, i) => (
              <li key={i}
                className="flex gap-3 items-start cursor-pointer group"
                onClick={() => toggleStep(i)}>
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-all"
                  style={{
                    background: checkedSteps.has(i) ? "var(--color-green)" : "transparent",
                    color: checkedSteps.has(i) ? "white" : "var(--color-green)",
                    border: checkedSteps.has(i) ? "none" : "2px solid var(--color-green)",
                  }}>
                  {checkedSteps.has(i) ? "✓" : i + 1}
                </div>
                <span className={`text-[13px] transition-all ${checkedSteps.has(i) ? "line-through opacity-50" : ""}`}>
                  {step}
                </span>
              </li>
            ))}
          </ol>
        </div>
      )}

      <div className="disclaimer text-center text-[12px]">
        These projections are estimates. Actual results depend on your effort, location, and market conditions.
      </div>
    </div>
  );
});
