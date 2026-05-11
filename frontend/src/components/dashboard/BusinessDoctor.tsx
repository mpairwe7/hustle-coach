"use client";

import type { DoctorResult } from "@/lib/api";
import { HealthScoreRing } from "./HealthRing";

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    healthy: "var(--color-green)",
    warning: "var(--color-gold)",
    critical: "var(--color-danger)",
  };
  return (
    <span
      className="inline-block w-2.5 h-2.5 rounded-full mr-2"
      style={{ background: colors[status] || "var(--color-text-muted)" }}
      aria-hidden="true"
    />
  );
}

interface BusinessDoctorProps {
  doctor: DoctorResult | null;
  loading: boolean;
  onRun: () => void;
}

export function BusinessDoctor({
  doctor,
  loading,
  onRun,
}: BusinessDoctorProps) {
  return (
    <div className="space-y-4 animate-fade-in">
      <div className="card text-center">
        <div
          className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl"
          style={{ background: "rgba(45,106,79,0.08)" }}
        >
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--color-green)"
            strokeWidth="1.5"
          >
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
          </svg>
        </div>
        <h3
          className="text-lg font-bold mb-2"
          style={{ color: "var(--color-green-dark)" }}
        >
          AI Business Doctor
        </h3>
        <p
          className="text-sm mb-4"
          style={{ color: "var(--color-text-muted)" }}
        >
          Get an instant health check-up for your business based on your
          profile data.
        </p>
        <button
          onClick={onRun}
          className="btn-primary"
          disabled={loading}
        >
          {loading ? "Analysing..." : "Run Check-Up"}
        </button>
      </div>

      {doctor && (
        <div className="space-y-4 animate-fade-in">
          <div className="card flex items-center gap-4">
            <HealthScoreRing score={doctor.health_score} size={80} />
            <div>
              <p
                className="font-bold text-lg capitalize"
                style={{ color: "var(--color-green-dark)" }}
              >
                {doctor.overall_health}
              </p>
              <p
                className="text-xs"
                style={{ color: "var(--color-text-muted)" }}
              >
                Overall Business Health
              </p>
            </div>
          </div>

          {doctor.diagnosis.map((d, i) => (
            <div key={i} className="card !p-3">
              <div className="flex items-center gap-2 mb-1">
                <StatusDot status={d.status} />
                <span
                  className="text-sm font-bold capitalize"
                  style={{ color: "var(--color-text)" }}
                >
                  {d.area}
                </span>
                <span
                  className={`badge text-[9px] badge-${d.priority === "urgent" || d.priority === "high" ? "low" : d.priority === "medium" ? "medium" : "high"}`}
                >
                  {d.priority}
                </span>
              </div>
              <p
                className="text-sm mb-1"
                style={{ color: "var(--color-text-muted)" }}
              >
                {d.finding}
              </p>
              <p
                className="text-sm font-medium"
                style={{ color: "var(--color-green)" }}
              >
                {d.recommendation}
              </p>
            </div>
          ))}

          {doctor.quick_wins.length > 0 && (
            <div className="card card-gold">
              <h4
                className="text-sm font-bold mb-2"
                style={{ color: "var(--color-gold-dark)" }}
              >
                Quick Wins (Do This Week)
              </h4>
              <ul className="space-y-1">
                {doctor.quick_wins.map((w, i) => (
                  <li key={i} className="text-sm flex items-start gap-2">
                    <span style={{ color: "var(--color-gold)" }}>
                      &#x2192;
                    </span>
                    <span style={{ color: "var(--color-text)" }}>{w}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <p className="disclaimer">{doctor.disclaimer}</p>
        </div>
      )}
    </div>
  );
}
