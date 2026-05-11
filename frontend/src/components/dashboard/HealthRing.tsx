"use client";

export function HealthScoreRing({
  score,
  size = 120,
}: {
  score: number;
  size?: number;
}) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color =
    score >= 75
      ? "var(--color-green)"
      : score >= 50
        ? "var(--color-gold)"
        : score >= 25
          ? "var(--color-earth)"
          : "var(--color-danger)";

  return (
    <div
      className="relative flex items-center justify-center"
      style={{ width: size, height: size }}
      role="meter"
      aria-valuenow={score}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label="Business health score"
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(0,0,0,0.06)"
          strokeWidth="10"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="progress-ring"
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-2xl font-extrabold" style={{ color }}>
          {score}
        </div>
        <div
          className="text-[10px]"
          style={{ color: "var(--color-text-muted)" }}
        >
          Health
        </div>
      </div>
    </div>
  );
}
