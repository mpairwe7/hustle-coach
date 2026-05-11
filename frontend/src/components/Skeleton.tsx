"use client";

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  circle?: boolean;
}

export function Skeleton({ className = "", width, height, circle }: SkeletonProps) {
  return (
    <div
      className={`skeleton ${circle ? "skeleton-circle" : ""} ${className}`}
      style={{ width, height }}
      aria-hidden="true"
    />
  );
}

export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div aria-hidden="true">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="skeleton skeleton-text"
          style={{ width: i === lines - 1 ? "60%" : `${85 + Math.random() * 15}%` }}
        />
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="skeleton-card" aria-hidden="true">
      <div className="skeleton skeleton-heading" />
      <SkeletonText lines={2} />
    </div>
  );
}

/** Chat message skeleton */
export function SkeletonMessage({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`} aria-hidden="true">
      <div style={{ maxWidth: isUser ? "60%" : "75%", width: "100%" }}>
        {!isUser && (
          <div className="flex items-center gap-2 mb-1.5">
            <Skeleton width={24} height={24} circle />
            <Skeleton width={80} height={14} />
          </div>
        )}
        <div
          className="skeleton"
          style={{
            height: isUser ? 42 : 80,
            borderRadius: "16px",
          }}
        />
      </div>
    </div>
  );
}

/** Dashboard stats skeleton */
export function SkeletonDashboard() {
  return (
    <div className="space-y-6" aria-label="Loading dashboard" aria-hidden="true">
      {/* Health score + stats */}
      <div className="card flex flex-col sm:flex-row items-center gap-6">
        <Skeleton width={120} height={120} circle />
        <div className="flex-1 grid grid-cols-2 gap-4 w-full">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i}>
              <Skeleton width="60%" height={28} className="mb-1" />
              <Skeleton width="80%" height={12} />
            </div>
          ))}
        </div>
      </div>
      {/* Progress bar */}
      <Skeleton height={12} className="!rounded-full" />
      {/* Tabs */}
      <Skeleton height={44} className="!rounded-lg" />
      {/* Cards */}
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    </div>
  );
}

/** Leaderboard skeleton */
export function SkeletonLeaderboard() {
  return (
    <div className="space-y-3" aria-hidden="true">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="card flex items-center gap-4 !p-3">
          <Skeleton width={40} height={40} circle />
          <div className="flex-1">
            <Skeleton width="50%" height={16} className="mb-1" />
            <Skeleton width="30%" height={12} />
          </div>
          <Skeleton width={60} height={20} />
        </div>
      ))}
    </div>
  );
}
