"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useChatStore } from "@/store/useChatStore";

const LOCALES = [
  { code: "en", label: "EN", name: "English" },
  { code: "lg", label: "LG", name: "Luganda" },
  { code: "sw", label: "SW", name: "Swahili" },
  { code: "nyn", label: "NY", name: "Runyankole" },
] as const;

const THEMES = [
  { value: "system", label: "System" },
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
] as const;

type ThemeValue = (typeof THEMES)[number]["value"];

function getStoredTheme(): ThemeValue {
  if (typeof window === "undefined") return "system";
  const stored = localStorage.getItem("hustle-scale-theme");
  if (stored === "dark" || stored === "light") return stored;
  return "system";
}

function getStoredTTSRate(): number {
  if (typeof window === "undefined") return 0.92;
  const stored = localStorage.getItem("hustle-scale-tts-rate");
  if (stored) {
    const parsed = parseFloat(stored);
    if (!isNaN(parsed) && parsed >= 0.5 && parsed <= 1.5) return parsed;
  }
  return 0.92;
}

function applyTheme(theme: ThemeValue) {
  if (theme === "system") {
    document.documentElement.removeAttribute("data-theme");
    localStorage.removeItem("hustle-scale-theme");
  } else {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("hustle-scale-theme", theme);
  }
}

export default function SettingsPage() {
  const locale = useChatStore((s) => s.locale);
  const setLocale = useChatStore((s) => s.setLocale);
  const clearChat = useChatStore((s) => s.clearChat);

  const [theme, setTheme] = useState<ThemeValue>("system");
  const [ttsRate, setTTSRate] = useState(0.92);
  const [showConfirm, setShowConfirm] = useState(false);
  const [cleared, setCleared] = useState(false);

  useEffect(() => {
    setTheme(getStoredTheme());
    setTTSRate(getStoredTTSRate());
  }, []);

  const handleThemeChange = useCallback((value: ThemeValue) => {
    setTheme(value);
    applyTheme(value);
  }, []);

  const handleTTSRateChange = useCallback((value: number) => {
    setTTSRate(value);
    localStorage.setItem("hustle-scale-tts-rate", String(value));
  }, []);

  const handleClearAll = useCallback(() => {
    clearChat();
    localStorage.clear();
    applyTheme("system");
    setTheme("system");
    setTTSRate(0.92);
    setShowConfirm(false);
    setCleared(true);
    setTimeout(() => setCleared(false), 2500);
  }, [clearChat]);

  return (
    <main
      id="main"
      className="min-h-screen has-bottom-nav"
      style={{ background: "var(--color-cream)" }}
    >
      {/* Header */}
      <header className="px-4 pt-6 pb-4 sm:px-8 sm:pt-10 sm:pb-6">
        <div className="mx-auto max-w-2xl">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm font-semibold no-underline mb-4"
            style={{ color: "var(--color-green)" }}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M19 12H5" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            Back to Home
          </Link>
          <h1
            className="text-2xl font-extrabold sm:text-3xl"
            style={{ color: "var(--color-green-dark)" }}
          >
            Settings
          </h1>
          <p
            className="mt-1 text-sm"
            style={{ color: "var(--color-text-muted)" }}
          >
            Customize your HustleScale experience
          </p>
        </div>
      </header>

      <div className="px-4 pb-16 sm:px-8">
        <div className="mx-auto max-w-2xl space-y-6">
          {/* Language Preference */}
          <section className="card">
            <h2
              className="text-base font-bold mb-1"
              style={{ color: "var(--color-text)" }}
            >
              Language
            </h2>
            <p
              className="text-sm mb-4"
              style={{ color: "var(--color-text-muted)" }}
            >
              Choose your preferred language for AI coaching
            </p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 sm:gap-3">
              {LOCALES.map((loc) => {
                const isActive = locale === loc.code;
                return (
                  <button
                    key={loc.code}
                    onClick={() => setLocale(loc.code)}
                    className="flex flex-col items-center gap-1 px-5 py-3 rounded-xl font-semibold text-sm transition-all"
                    style={{
                      background: isActive
                        ? "linear-gradient(135deg, var(--color-green), var(--color-green-dark))"
                        : "rgba(45,106,79,0.06)",
                      color: isActive ? "white" : "var(--color-green)",
                      border: isActive
                        ? "2px solid var(--color-green)"
                        : "2px solid transparent",
                      cursor: "pointer",
                      minWidth: "72px",
                    }}
                  >
                    <span className="text-lg font-bold">{loc.label}</span>
                    <span
                      className="text-xs"
                      style={{
                        color: isActive
                          ? "rgba(255,255,255,0.7)"
                          : "var(--color-text-muted)",
                      }}
                    >
                      {loc.name}
                    </span>
                  </button>
                );
              })}
            </div>
          </section>

          {/* Theme */}
          <section className="card">
            <h2
              className="text-base font-bold mb-1"
              style={{ color: "var(--color-text)" }}
            >
              Theme
            </h2>
            <p
              className="text-sm mb-4"
              style={{ color: "var(--color-text-muted)" }}
            >
              Switch between light and dark appearance
            </p>
            <div className="flex flex-wrap gap-3">
              {THEMES.map((t) => {
                const isActive = theme === t.value;
                return (
                  <button
                    key={t.value}
                    onClick={() => handleThemeChange(t.value)}
                    className="flex items-center gap-2 px-5 py-3 rounded-xl font-semibold text-sm transition-all"
                    style={{
                      background: isActive
                        ? "linear-gradient(135deg, var(--color-green), var(--color-green-dark))"
                        : "rgba(45,106,79,0.06)",
                      color: isActive ? "white" : "var(--color-green)",
                      border: isActive
                        ? "2px solid var(--color-green)"
                        : "2px solid transparent",
                      cursor: "pointer",
                      minWidth: "90px",
                      justifyContent: "center",
                    }}
                  >
                    {t.value === "system" && (
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <rect x="2" y="3" width="20" height="14" rx="2" />
                        <line x1="8" y1="21" x2="16" y2="21" />
                        <line x1="12" y1="17" x2="12" y2="21" />
                      </svg>
                    )}
                    {t.value === "light" && (
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <circle cx="12" cy="12" r="5" />
                        <line x1="12" y1="1" x2="12" y2="3" />
                        <line x1="12" y1="21" x2="12" y2="23" />
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                        <line x1="1" y1="12" x2="3" y2="12" />
                        <line x1="21" y1="12" x2="23" y2="12" />
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                      </svg>
                    )}
                    {t.value === "dark" && (
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
                      </svg>
                    )}
                    {t.label}
                  </button>
                );
              })}
            </div>
          </section>

          {/* Voice Settings */}
          <section className="card">
            <h2
              className="text-base font-bold mb-1"
              style={{ color: "var(--color-text)" }}
            >
              Voice Settings
            </h2>
            <p
              className="text-sm mb-4"
              style={{ color: "var(--color-text-muted)" }}
            >
              Adjust the text-to-speech playback speed
            </p>
            <div>
              <div className="flex items-center justify-between mb-2">
                <label
                  htmlFor="tts-rate"
                  className="text-sm font-semibold"
                  style={{ color: "var(--color-text)" }}
                >
                  TTS Speed
                </label>
                <span
                  className="text-sm font-bold px-3 py-1 rounded-lg"
                  style={{
                    background: "rgba(45,106,79,0.08)",
                    color: "var(--color-green)",
                  }}
                >
                  {ttsRate.toFixed(2)}x
                </span>
              </div>
              <input
                id="tts-rate"
                type="range"
                min="0.5"
                max="1.5"
                step="0.01"
                value={ttsRate}
                onChange={(e) =>
                  handleTTSRateChange(parseFloat(e.target.value))
                }
                className="w-full"
                style={{
                  accentColor: "var(--color-green)",
                }}
              />
              <div
                className="flex justify-between text-xs mt-1"
                style={{ color: "var(--color-text-light)" }}
              >
                <span>0.5x Slow</span>
                <span>0.92x Default</span>
                <span>1.5x Fast</span>
              </div>
            </div>
          </section>

          {/* Clear All Data */}
          <section className="card" style={{ borderColor: "rgba(239,68,68,0.2)" }}>
            <h2
              className="text-base font-bold mb-1"
              style={{ color: "var(--color-danger)" }}
            >
              Clear All Data
            </h2>
            <p
              className="text-sm mb-4"
              style={{ color: "var(--color-text-muted)" }}
            >
              This will permanently delete your chat history, authentication,
              and all local settings. This action cannot be undone.
            </p>
            <button
              onClick={() => setShowConfirm(true)}
              className="px-5 py-3 rounded-xl font-semibold text-sm transition-all"
              style={{
                background: "rgba(239,68,68,0.08)",
                color: "var(--color-danger)",
                border: "1.5px solid rgba(239,68,68,0.3)",
                cursor: "pointer",
              }}
            >
              Clear All Data
            </button>

            {cleared && (
              <p
                className="mt-3 text-sm font-semibold animate-fade-in"
                style={{ color: "var(--color-green)" }}
              >
                All data cleared successfully.
              </p>
            )}
          </section>
        </div>
      </div>

      {/* Confirmation Dialog */}
      {showConfirm && (
        <div className="confirm-overlay" onClick={() => setShowConfirm(false)}>
          <div
            className="confirm-dialog"
            onClick={(e) => e.stopPropagation()}
          >
            <h3
              className="text-lg font-bold mb-2"
              style={{ color: "var(--color-text)" }}
            >
              Clear all data?
            </h3>
            <p
              className="text-sm mb-6"
              style={{ color: "var(--color-text-muted)" }}
            >
              This will delete your chat history, authentication session, and
              all preferences. You will need to set up everything again.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowConfirm(false)}
                className="btn-ghost text-sm font-semibold px-4 py-2"
              >
                Cancel
              </button>
              <button
                onClick={handleClearAll}
                className="px-5 py-3 rounded-xl font-semibold text-sm"
                style={{
                  background:
                    "linear-gradient(135deg, var(--color-danger), #dc2626)",
                  color: "white",
                  border: "none",
                  cursor: "pointer",
                }}
              >
                Yes, Clear Everything
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
