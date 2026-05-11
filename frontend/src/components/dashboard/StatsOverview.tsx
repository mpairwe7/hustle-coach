"use client";

import type { BusinessProfile } from "@/lib/api";
import { HealthScoreRing } from "./HealthRing";

interface StatsOverviewProps {
  healthScore: number;
  completedMilestones: number;
  totalMilestones: number;
  profile: BusinessProfile;
}

export function StatsOverview({
  healthScore,
  completedMilestones,
  totalMilestones,
  profile,
}: StatsOverviewProps) {
  const progressPct = Math.round(
    (completedMilestones / Math.max(totalMilestones, 1)) * 100,
  );

  return (
    <>
      {/* Health Score + Stats */}
      <div className="card flex flex-col sm:flex-row items-center gap-6">
        <HealthScoreRing score={healthScore} />
        <div className="flex-1 grid grid-cols-2 gap-4 w-full">
          <div>
            <div
              className="stat-value"
              style={{ color: "var(--color-green)" }}
            >
              {completedMilestones}/{totalMilestones}
            </div>
            <div className="stat-label">Milestones Done</div>
          </div>
          <div>
            <div
              className="stat-value"
              style={{ color: "var(--color-gold)" }}
            >
              {profile.monthly_revenue_ugx > 0
                ? `${(profile.monthly_revenue_ugx / 1000).toFixed(0)}K`
                : "--"}
            </div>
            <div className="stat-label">Monthly Revenue (UGX)</div>
          </div>
          <div>
            <div
              className="stat-value"
              style={{
                color:
                  profile.monthly_profit_ugx >= 0
                    ? "var(--color-green)"
                    : "var(--color-danger)",
              }}
            >
              {profile.monthly_profit_ugx !== 0
                ? `${(profile.monthly_profit_ugx / 1000).toFixed(0)}K`
                : "--"}
            </div>
            <div className="stat-label">Monthly Profit (UGX)</div>
          </div>
          <div>
            <div
              className="stat-value"
              style={{ color: "var(--color-earth)" }}
            >
              {profile.employees || 0}
            </div>
            <div className="stat-label">Employees</div>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div>
        <div className="flex justify-between text-xs mb-1">
          <span style={{ color: "var(--color-text-muted)" }}>
            Business Journey Progress
          </span>
          <span className="font-bold" style={{ color: "var(--color-green)" }}>
            {progressPct}%
          </span>
        </div>
        <div
          className="h-3 rounded-full overflow-hidden"
          style={{ background: "rgba(45,106,79,0.1)" }}
          role="progressbar"
          aria-valuenow={progressPct}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${progressPct}%`,
              background:
                "linear-gradient(90deg, var(--color-green), var(--color-gold))",
            }}
          />
        </div>
      </div>
    </>
  );
}
