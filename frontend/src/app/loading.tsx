export default function Loading() {
  return (
    <div
      className="flex min-h-dvh items-center justify-center"
      style={{ background: "var(--color-cream)" }}
    >
      <div className="flex flex-col items-center gap-4">
        <div
          className="flex h-14 w-14 items-center justify-center rounded-2xl"
          style={{
            background:
              "linear-gradient(135deg, var(--color-green), var(--color-green-dark))",
            boxShadow: "0 6px 24px rgba(45,106,79,0.2)",
          }}
        >
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="white"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="animate-spin-slow"
          >
            <path d="M12 3v18M3 12l3-3 3 3M15 12l3-3 3 3M6 9v9a3 3 0 003 3h6a3 3 0 003-3V9" />
          </svg>
        </div>
        <div className="typing-dots">
          <span />
          <span />
          <span />
        </div>
      </div>
    </div>
  );
}
