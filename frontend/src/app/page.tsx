"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { leaderboardApi } from "@/lib/api";
import type { ImpactStats } from "@/lib/api";

const FEATURES = [
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
    ),
    title: "AI Business Plans",
    desc: "Describe your idea, get a complete plan with budget, pricing, break-even analysis, and marketing script in minutes",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
      </svg>
    ),
    title: "Business Doctor",
    desc: "Submit your numbers and get an instant health diagnosis with actionable recommendations to grow",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-gold)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="1" x2="12" y2="23" />
        <path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
      </svg>
    ),
    title: "Funding Matcher",
    desc: "Find YLP, Emyooga, UWEP, PDM grants, micro-loans, and VSLAs you qualify for with step-by-step guides",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
        <rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
      </svg>
    ),
    title: "Progress Dashboard",
    desc: "Track milestones from idea to launch, monitor revenue, and celebrate every step forward",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-earth)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2a3 3 0 00-3 3v7a3 3 0 006 0V5a3 3 0 00-3-3z" />
        <path d="M19 10v2a7 7 0 01-14 0v-2" /><line x1="12" y1="19" x2="12" y2="22" />
      </svg>
    ),
    title: "Voice First",
    desc: "Speak in Luganda, Runyankole, Swahili, or English — natural code-switching supported",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" />
      </svg>
    ),
    title: "Cooperative Matcher",
    desc: "Find group business models, form VSLAs, and pool resources with other youth for bulk buying power",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-gold)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    ),
    title: "Market Intelligence",
    desc: "Real-time UGX prices for 45+ items across poultry, agriculture, construction, telecoms, and more",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-gold)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M6 9H4.5a2.5 2.5 0 010-5C7 4 7 7 7 7" />
        <path d="M18 9h1.5a2.5 2.5 0 000-5C17 4 17 7 17 7" />
        <path d="M4 22h16" /><path d="M18 2H6v7a6 6 0 0012 0V2Z" />
      </svg>
    ),
    title: "National Leaderboard",
    desc: "Join thousands of young Ugandans building businesses — earn badges and inspire your community",
  },
];

const BUSINESSES = [
  "Poultry Farming",
  "Tailoring",
  "Mobile Money",
  "Boda Repair",
  "Salon",
  "Rolex Vending",
  "Fish Farming",
  "Welding",
  "Juice Making",
  "Urban Farming",
  "Phone Repair",
  "Digital Services",
  "Agro-Processing",
  "Restaurants",
  "Crafts & Pottery",
  "Tutoring",
];

const IMPACT_DEFAULTS: ImpactStats = {
  total_users: 0,
  businesses_planned: 0,
  businesses_launched: 0,
  jobs_created: 0,
};

function ImpactCounter({
  label,
  value,
  suffix = "",
}: {
  label: string;
  value: number;
  suffix?: string;
}) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (value === 0) return;
    const duration = 1500;
    const steps = 40;
    const increment = value / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= value) {
        setCount(value);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [value]);

  return (
    <div className="text-center">
      <div
        className="text-3xl sm:text-4xl font-extrabold"
        style={{ color: "var(--color-gold)" }}
      >
        {count > 0 ? count.toLocaleString() : "--"}
        {suffix}
      </div>
      <div
        className="text-xs sm:text-sm mt-1"
        style={{ color: "var(--color-text-muted)" }}
      >
        {label}
      </div>
    </div>
  );
}

export default function LandingPage() {
  const [impact, setImpact] = useState<ImpactStats>(IMPACT_DEFAULTS);

  useEffect(() => {
    leaderboardApi.impact().then(setImpact).catch(() => {});
  }, []);

  return (
    <main
      id="main"
      className="min-h-screen has-bottom-nav"
      style={{ background: "var(--color-cream)" }}
    >
      {/* Hero */}
      <section className="relative overflow-hidden px-4 pt-12 pb-16 sm:px-8 sm:pt-20 sm:pb-24">
        <div
          className="absolute inset-0 -z-10"
          style={{
            background:
              "radial-gradient(ellipse at 30% 20%, rgba(45,106,79,0.10) 0%, transparent 60%), " +
              "radial-gradient(ellipse at 70% 80%, rgba(212,160,23,0.08) 0%, transparent 60%)",
          }}
        />

        <div className="mx-auto max-w-4xl text-center">
          <div
            className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl"
            style={{
              background:
                "linear-gradient(135deg, var(--color-green), var(--color-green-dark))",
              boxShadow: "0 8px 32px rgba(45,106,79,0.25)",
            }}
          >
            <svg
              width="40"
              height="40"
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

          <div className="mb-3 flex items-center justify-center gap-2">
            <span className="badge-high text-[10px] tracking-wider px-3 py-1">
              CLAUDE HACKATHON MAKERERE 2026
            </span>
          </div>

          <h1
            className="mb-3 text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl"
            style={{ color: "var(--color-green-dark)" }}
          >
            HustleScale
          </h1>

          <p
            className="mb-2 text-lg font-semibold sm:text-xl"
            style={{ color: "var(--color-gold-dark)" }}
          >
            The National Youth Micro-Enterprise Accelerator
          </p>

          <p
            className="mx-auto mb-8 max-w-2xl text-base sm:text-lg"
            style={{ color: "var(--color-text-muted)" }}
          >
            Empowering Uganda&apos;s youth (18-30) to turn business ideas into
            sustainable, scalable micro-enterprises. AI-powered business plans,
            funding access, progress tracking, and real market intelligence —
            in your language, on your phone, even offline.
          </p>

          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/chat"
              className="btn-gold text-lg px-8 py-4 no-underline"
            >
              Start Your Hustle
            </Link>
            <Link href="/dashboard" className="btn-outline no-underline">
              My Dashboard
            </Link>
            <a
              href="#features"
              className="btn-ghost text-sm no-underline font-semibold"
              style={{ color: "var(--color-green)" }}
            >
              Learn More
            </a>
          </div>

          {/* Business tags */}
          <div className="mt-10 flex flex-wrap justify-center gap-2">
            {BUSINESSES.map((biz) => (
              <span
                key={biz}
                className="rounded-full px-4 py-1.5 text-sm font-medium"
                style={{
                  background: "rgba(45,106,79,0.08)",
                  color: "var(--color-green)",
                }}
              >
                {biz}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Impact Stats */}
      <section
        className="px-4 py-12 sm:px-8"
        style={{
          background:
            "linear-gradient(135deg, var(--color-green-dark), var(--color-green))",
        }}
      >
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-8 text-center text-xl font-bold text-white sm:text-2xl">
            Powering Uganda Toward a $500 Billion Economy
          </h2>
          <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
            <ImpactCounter
              label="Youth Entrepreneurs"
              value={impact.total_users}
              suffix="+"
            />
            <ImpactCounter
              label="Business Plans Created"
              value={impact.businesses_planned}
            />
            <ImpactCounter
              label="Businesses Launched"
              value={impact.businesses_launched}
            />
            <ImpactCounter
              label="Jobs Created"
              value={impact.jobs_created}
            />
          </div>
        </div>
      </section>

      {/* Features */}
      <section
        id="features"
        className="px-4 py-16 sm:px-8"
        style={{ background: "var(--color-warm-white)" }}
      >
        <div className="mx-auto max-w-6xl">
          <h2
            className="mb-3 text-center text-2xl font-bold sm:text-3xl"
            style={{ color: "var(--color-green-dark)" }}
          >
            Your Complete Business Accelerator
          </h2>
          <p
            className="mb-10 text-center text-sm sm:text-base"
            style={{ color: "var(--color-text-muted)" }}
          >
            Everything you need to go from idea to income — no experience
            required
          </p>

          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((f) => (
              <div key={f.title} className="card">
                <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl" style={{ background: "rgba(45,106,79,0.06)" }}>
                  {f.icon}
                </div>
                <h3
                  className="mb-2 text-base font-bold"
                  style={{ color: "var(--color-text)" }}
                >
                  {f.title}
                </h3>
                <p
                  className="text-sm"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  {f.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="px-4 py-16 sm:px-8">
        <div className="mx-auto max-w-3xl">
          <h2
            className="mb-10 text-center text-2xl font-bold sm:text-3xl"
            style={{ color: "var(--color-green-dark)" }}
          >
            From Idea to Income in 4 Steps
          </h2>

          <div className="space-y-8">
            {[
              {
                step: "1",
                title: "Tell us your idea",
                desc: 'Type or speak: "I want to start a poultry farm with UGX 1 million near Mukono" — in any language.',
              },
              {
                step: "2",
                title: "Get your business plan + funding",
                desc: "Receive a detailed plan with real UGX prices, break-even analysis, plus matching government funds and grants.",
              },
              {
                step: "3",
                title: "Track your progress",
                desc: "Check off milestones, update your revenue, get AI Business Doctor check-ups, and see your health score grow.",
              },
              {
                step: "4",
                title: "Scale and inspire",
                desc: "Join the national leaderboard, form cooperatives for bulk buying, and become a success story for other youth.",
              },
            ].map((item) => (
              <div key={item.step} className="flex gap-4 items-start">
                <div
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full text-lg font-bold text-white"
                  style={{
                    background:
                      "linear-gradient(135deg, var(--color-green), var(--color-gold))",
                  }}
                >
                  {item.step}
                </div>
                <div>
                  <h3
                    className="text-lg font-bold"
                    style={{ color: "var(--color-text)" }}
                  >
                    {item.title}
                  </h3>
                  <p style={{ color: "var(--color-text-muted)" }}>
                    {item.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-12 text-center">
            <Link
              href="/chat"
              className="btn-primary text-lg px-8 py-4 no-underline"
            >
              Start Now — It&apos;s Free
            </Link>
          </div>
        </div>
      </section>

      {/* Success Stories Preview */}
      <section
        className="px-4 py-16 sm:px-8"
        style={{ background: "rgba(212,160,23,0.04)" }}
      >
        <div className="mx-auto max-w-5xl">
          <h2
            className="mb-10 text-center text-2xl font-bold sm:text-3xl"
            style={{ color: "var(--color-green-dark)" }}
          >
            Real Ugandan Youth, Real Results
          </h2>
          <div className="grid gap-6 sm:grid-cols-3">
            {[
              {
                name: "Sarah N., 24",
                biz: "Poultry Farming",
                loc: "Mukono",
                result: "50 to 600 broilers, UGX 1.2M/month",
                badge: "community_builder",
              },
              {
                name: "Brian O., 22",
                biz: "Street Food to Catering",
                loc: "Kampala",
                result: "Rolex cart to event catering, UGX 2M+/month",
                badge: "rising_star",
              },
              {
                name: "Grace A., 26",
                biz: "Tailoring",
                loc: "Mbarara",
                result: "School uniform contracts, UGX 1.8M peak/month",
                badge: "consistent_hustler",
              },
            ].map((s) => (
              <div key={s.name} className="card card-gold">
                <div className="flex items-center gap-2 mb-3">
                  <div
                    className="h-10 w-10 rounded-full flex items-center justify-center text-lg font-bold text-white"
                    style={{
                      background:
                        "linear-gradient(135deg, var(--color-green), var(--color-gold))",
                    }}
                  >
                    {s.name.charAt(0)}
                  </div>
                  <div>
                    <p
                      className="font-bold text-sm"
                      style={{ color: "var(--color-text)" }}
                    >
                      {s.name}
                    </p>
                    <p
                      className="text-xs"
                      style={{ color: "var(--color-text-muted)" }}
                    >
                      {s.biz} — {s.loc}
                    </p>
                  </div>
                </div>
                <p
                  className="text-sm font-semibold"
                  style={{ color: "var(--color-green)" }}
                >
                  {s.result}
                </p>
              </div>
            ))}
          </div>
          <div className="mt-8 text-center">
            <Link href="/leaderboard" className="btn-outline no-underline">
              View All Success Stories
            </Link>
          </div>
        </div>
      </section>

      {/* Ethical Note */}
      <section
        className="px-4 py-12 sm:px-8"
        style={{ background: "rgba(212,160,23,0.06)" }}
      >
        <div className="mx-auto max-w-2xl text-center">
          <p
            className="text-sm italic"
            style={{ color: "var(--color-text-muted)" }}
          >
            HustleScale is an AI tool — not a replacement for real mentorship.
            We encourage you to seek guidance from successful business owners in
            your community. No business is guaranteed to succeed. Success
            requires hard work, learning from mistakes, and patience. Ubuntu:
            &ldquo;I am because we are.&rdquo;
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer
        className="px-4 py-8 sm:px-8"
        style={{
          background: "var(--color-green-dark)",
          color: "rgba(255,255,255,0.7)",
        }}
      >
        <div className="mx-auto max-w-5xl">
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-between">
            <div className="text-center sm:text-left">
              <p className="text-lg font-bold text-white">HustleScale</p>
              <p className="text-sm">
                The National Youth Micro-Enterprise Accelerator
              </p>
            </div>
            <div className="flex gap-4 text-sm">
              <Link
                href="/chat"
                className="text-white/80 hover:text-white no-underline"
              >
                AI Coach
              </Link>
              <Link
                href="/dashboard"
                className="text-white/80 hover:text-white no-underline"
              >
                Dashboard
              </Link>
              <Link
                href="/leaderboard"
                className="text-white/80 hover:text-white no-underline"
              >
                Leaderboard
              </Link>
            </div>
          </div>
          <div className="mt-6 pt-4 border-t border-white/10 text-center text-xs">
            <p>
              Built with Ubuntu philosophy: &ldquo;I am because we
              are.&rdquo;
            </p>
            <p className="mt-1">
              Claude Hackathon Makerere 2026 — Powering Uganda&apos;s $500B
              Economy
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
