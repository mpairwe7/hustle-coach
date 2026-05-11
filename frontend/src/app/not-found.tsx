import Link from "next/link";

export default function NotFound() {
  return (
    <div
      className="flex min-h-dvh flex-col items-center justify-center gap-6 px-4"
      style={{ background: "var(--color-cream)" }}
    >
      <div className="card mx-auto max-w-md w-full p-8 text-center">
        <div
          className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl text-2xl"
          style={{
            background:
              "linear-gradient(135deg, var(--color-green), var(--color-green-dark))",
          }}
        >
          <svg
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
            <line x1="8" y1="11" x2="14" y2="11" />
          </svg>
        </div>

        <h1
          className="text-4xl font-extrabold mb-2"
          style={{ color: "var(--color-green-dark)" }}
        >
          404
        </h1>
        <p
          className="text-lg font-semibold mb-1"
          style={{ color: "var(--color-text)" }}
        >
          Page not found
        </p>
        <p
          className="text-sm mb-6"
          style={{ color: "var(--color-text-muted)" }}
        >
          This page doesn&apos;t exist. Let&apos;s get you back to building your
          hustle.
        </p>

        <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Link href="/chat" className="btn-primary no-underline">
            Start Chatting
          </Link>
          <Link href="/" className="btn-outline no-underline">
            Go Home
          </Link>
        </div>
      </div>
    </div>
  );
}
