"use client";

import Link from "next/link";
import { SkeletonDashboard } from "@/components/Skeleton";

/**
 * Shown while dashboard data is being fetched.
 */
export function DashboardLoadingShell() {
  return (
    <div
      className="min-h-dvh has-bottom-nav"
      style={{
        background:
          "linear-gradient(180deg, var(--color-cream) 0%, #F5ECD7 100%)",
      }}
    >
      <header
        className="glass"
        style={{ borderBottom: "1px solid rgba(245,230,200,0.4)" }}
      >
        <div className="mx-auto max-w-3xl flex items-center px-4 py-3">
          <div className="skeleton" style={{ width: 160, height: 24 }} />
        </div>
      </header>
      <div className="mx-auto max-w-3xl px-4 py-6">
        <SkeletonDashboard />
      </div>
    </div>
  );
}

/**
 * Shown when the dashboard API call fails.
 */
export function DashboardErrorShell({ onRetry }: { onRetry: () => void }) {
  return (
    <div
      className="flex min-h-dvh flex-col items-center justify-center gap-6 px-4 has-bottom-nav"
      style={{ background: "var(--color-cream)" }}
      id="main"
    >
      <div className="card text-center max-w-md w-full p-8">
        <div
          className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl"
          style={{ background: "rgba(239,68,68,0.08)" }}
        >
          <svg
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--color-danger)"
            strokeWidth="2"
            strokeLinecap="round"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>
        <h1
          className="text-xl font-bold mb-2"
          style={{ color: "var(--color-text)" }}
        >
          Could not load dashboard
        </h1>
        <p
          className="text-sm mb-6"
          style={{ color: "var(--color-text-muted)" }}
        >
          Please check your connection and try again.
        </p>
        <button onClick={onRetry} className="btn-primary w-full">
          Retry
        </button>
      </div>
    </div>
  );
}

/**
 * Shown when the user is not authenticated.
 */
export function DashboardAuthShell() {
  return (
    <div
      className="flex min-h-dvh flex-col items-center justify-center gap-6 px-4 has-bottom-nav"
      style={{ background: "var(--color-cream)" }}
      id="main"
    >
      <div className="card text-center max-w-md w-full p-8">
        <div
          className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl"
          style={{ background: "rgba(45,106,79,0.08)" }}
        >
          <svg
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--color-green)"
            strokeWidth="1.5"
          >
            <rect x="3" y="3" width="7" height="7" />
            <rect x="14" y="3" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" />
            <rect x="14" y="14" width="7" height="7" />
          </svg>
        </div>
        <h1
          className="text-2xl font-bold mb-2"
          style={{ color: "var(--color-green-dark)" }}
        >
          Your Dashboard
        </h1>
        <p
          className="text-sm mb-6"
          style={{ color: "var(--color-text-muted)" }}
        >
          Sign in to track your business journey, view milestones, and get AI
          health check-ups.
        </p>
        <Link href="/auth" className="btn-primary w-full no-underline">
          Sign In / Sign Up
        </Link>
        <Link
          href="/chat"
          className="btn-ghost mt-3 text-sm no-underline block"
          style={{ color: "var(--color-green)" }}
        >
          Continue without account
        </Link>
      </div>
    </div>
  );
}
