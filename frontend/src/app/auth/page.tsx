"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

export default function AuthPage() {
  const router = useRouter();
  const loginStore = useAuthStore((s) => s.login);

  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const data = isLogin
        ? await authApi.login(email, password)
        : await authApi.signup(email, password, name);

      // Store handles localStorage sync
      loginStore(data.token, data.user_id, data.name, data.credits);

      setSuccess(
        isLogin
          ? "Welcome back! Redirecting..."
          : `Account created with ${data.credits} free credits! Redirecting...`,
      );
      setTimeout(() => router.push("/dashboard"), 800);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main
      className="flex min-h-dvh items-center justify-center px-4 has-bottom-nav"
      style={{ background: "var(--color-cream)" }}
      id="main"
    >
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 text-center">
          <div
            className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl"
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
            >
              <path d="M12 3v18M3 12l3-3 3 3M15 12l3-3 3 3M6 9v9a3 3 0 003 3h6a3 3 0 003-3V9" />
            </svg>
          </div>
          <h1
            className="text-2xl font-bold"
            style={{ color: "var(--color-green-dark)" }}
          >
            {isLogin ? "Welcome back" : "Create your account"}
          </h1>
          <p
            className="mt-1 text-sm"
            style={{ color: "var(--color-text-muted)" }}
          >
            {isLogin
              ? "Sign in to continue your business journey"
              : "Start your entrepreneurship journey today"}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="card space-y-4">
          {!isLogin && (
            <div>
              <label
                className="mb-1 block text-sm font-medium"
                htmlFor="name"
              >
                Full Name
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input-field"
                placeholder="e.g., Sarah Namugga"
                autoComplete="name"
              />
            </div>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field"
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div>
            <label
              className="mb-1 block text-sm font-medium"
              htmlFor="password"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field"
              placeholder="At least 6 characters"
              minLength={6}
              required
              autoComplete={isLogin ? "current-password" : "new-password"}
            />
          </div>

          {error && (
            <div
              className="rounded-lg p-3 text-sm"
              style={{
                background: "rgba(211,47,47,0.08)",
                color: "var(--color-danger)",
              }}
              role="alert"
            >
              {error}
            </div>
          )}

          {success && (
            <div
              className="rounded-lg p-3 text-sm"
              style={{
                background: "rgba(45,106,79,0.08)",
                color: "var(--color-green)",
              }}
              role="status"
            >
              {success}
            </div>
          )}

          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? "Please wait..." : isLogin ? "Sign In" : "Create Account"}
          </button>

          <p
            className="text-center text-sm"
            style={{ color: "var(--color-text-muted)" }}
          >
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError("");
                setSuccess("");
              }}
              className="font-semibold underline"
              style={{ color: "var(--color-green)" }}
            >
              {isLogin ? "Sign up free" : "Sign in"}
            </button>
          </p>
        </form>

        <p
          className="mt-4 text-center text-sm"
          style={{ color: "var(--color-text-muted)" }}
        >
          <Link href="/chat" className="underline">
            Continue without account
          </Link>
        </p>
      </div>
    </main>
  );
}
