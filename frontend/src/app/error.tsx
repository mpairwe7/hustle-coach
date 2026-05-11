"use client";

import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div
      className="flex min-h-dvh flex-col items-center justify-center gap-6 px-4"
      style={{ background: "var(--color-cream)" }}
    >
      <div className="card mx-auto max-w-md w-full p-8 text-center">
        <div
          className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl text-2xl"
          style={{ background: "rgba(239,68,68,0.1)" }}
        >
          <svg
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--color-danger)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
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
          Something went wrong
        </h1>

        <p
          className="text-sm mb-6"
          style={{ color: "var(--color-text-muted)" }}
        >
          {error.message || "An unexpected error occurred. Please try again."}
        </p>

        <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
          <button onClick={reset} className="btn-primary">
            Try Again
          </button>
          <Link href="/" className="btn-outline no-underline">
            Go Home
          </Link>
        </div>
      </div>
    </div>
  );
}
