"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeftIcon } from "@/components/Icons";
import { SkeletonLeaderboard } from "@/components/Skeleton";
import { leaderboardApi } from "@/lib/api";
import type { LeaderboardData } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

const BADGE_INFO: Record<
  string,
  { emoji: string; label: string; color: string }
> = {
  rising_star: {
    emoji: "⭐",
    label: "Rising Star",
    color: "var(--color-gold)",
  },
  consistent_hustler: {
    emoji: "💪",
    label: "Consistent Hustler",
    color: "var(--color-green)",
  },
  community_builder: {
    emoji: "🤝",
    label: "Community Builder",
    color: "var(--color-earth)",
  },
};

const STAGE_COLORS: Record<string, string> = {
  idea: "var(--color-text-muted)",
  planning: "var(--color-gold)",
  launched: "var(--color-green-light)",
  growing: "var(--color-green)",
  scaling: "var(--color-green-dark)",
};

const STORY_CATEGORIES = [
  "All",
  "Poultry",
  "Catering",
  "Tailoring",
  "Mobile Money",
  "Salon",
] as const;

type StoryCategory = (typeof STORY_CATEGORIES)[number];

/** Map each filter pill to keywords that match the story business field */
const CATEGORY_KEYWORDS: Record<Exclude<StoryCategory, "All">, string[]> = {
  Poultry: ["poultry"],
  Catering: ["catering", "food", "rolex"],
  Tailoring: ["tailoring", "uniform", "sewing"],
  "Mobile Money": ["mobile money", "boda"],
  Salon: ["salon", "hair", "braiding"],
};

const SUCCESS_STORIES = [
  {
    name: "Sarah Namugga, 24",
    location: "Mukono",
    business: "Poultry Farming",
    story:
      "I started with 50 broiler chicks and UGX 800,000 from my savings. The first batch was scary \u2014 I lost 5 chicks to Newcastle disease before I learned about vaccination schedules. Now I manage 600 broilers, supply 3 restaurants, and earn UGX 1.2M per month. My secret? I never mixed business money with personal money, and I always reinvested 30% of profits.",
    revenue: "UGX 1.2M/month",
    started_with: "UGX 800,000",
    time: "18 months",
    key_lesson:
      "Vaccination schedule is everything. One disease outbreak can wipe out your entire investment.",
  },
  {
    name: "Brian Ochieng, 22",
    location: "Kampala",
    business: "Street Food to Event Catering",
    story:
      'I started selling rolex on a borrowed stall near Makerere University. Students loved my big portions. When someone asked me to cater their birthday, I said yes even though I had never done it. That one event led to 3 more referrals. Now I cater for corporate events and weddings, earning UGX 2M+ monthly.',
    revenue: "UGX 2M+/month",
    started_with: "UGX 200,000",
    time: "14 months",
    key_lesson:
      "Say yes to opportunities even when you are scared. Every big business started small.",
  },
  {
    name: "Grace Atuhaire, 26",
    location: "Mbarara",
    business: "Tailoring (School Uniforms)",
    story:
      "I borrowed a sewing machine from my aunt and started making simple dresses. When I noticed all the parents struggling to find school uniforms before term, I went to 5 schools and offered to make uniforms at 10% less than the shops. Now I have contracts with 3 schools and hire 2 extra tailors during peak season.",
    revenue: "UGX 1.8M peak/month",
    started_with: "Borrowed sewing machine",
    time: "12 months",
    key_lesson:
      "Find the pain point. Parents needed affordable uniforms \u2014 I solved that specific problem.",
  },
  {
    name: "Moses Ssempijja, 28",
    location: "Kawempe, Kampala",
    business: "Mobile Money + Boda Repair",
    story:
      "I noticed that boda riders in my area had nowhere to repair their bikes AND do mobile money. So I combined both services in one location. Riders come to fix their bikes and while waiting, they do mobile money transactions. The two businesses feed each other perfectly. Combined I earn UGX 1.2M/month.",
    revenue: "UGX 1.2M/month",
    started_with: "UGX 1.5M",
    time: "10 months",
    key_lesson:
      "Complementary businesses in one location create a flywheel effect \u2014 each brings customers for the other.",
  },
  {
    name: "Anita Nakirya, 23",
    location: "Nansana",
    business: "Hair Salon",
    story:
      "I started braiding hair under a mango tree with just 3 packets of braiding hair. My first customers were my neighbours. I saved every shilling and after 4 months rented a small room. Now I have a 3-chair salon, train apprentices, and earn UGX 1.5M per month. I still braid under the tree on market days for extra income.",
    revenue: "UGX 1.5M/month",
    started_with: "UGX 150,000",
    time: "11 months",
    key_lesson:
      "Start where you are with what you have. The mango tree was my first shop \u2014 and it still makes me money.",
  },
];

export default function LeaderboardPage() {
  const [data, setData] = useState<LeaderboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [tab, setTab] = useState<"leaderboard" | "stories">("leaderboard");
  const [storyFilter, setStoryFilter] = useState<StoryCategory>("All");

  const userName = useAuthStore((s) => s.userName);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  const filteredStories =
    storyFilter === "All"
      ? SUCCESS_STORIES
      : SUCCESS_STORIES.filter((s) => {
          const keywords = CATEGORY_KEYWORDS[storyFilter];
          const biz = s.business.toLowerCase();
          return keywords.some((kw) => biz.includes(kw));
        });

  const fetchData = useCallback(() => {
    setError(false);
    setLoading(true);
    leaderboardApi
      .get()
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div
      className="min-h-dvh has-bottom-nav"
      style={{
        background:
          "linear-gradient(180deg, var(--color-cream) 0%, #F5ECD7 100%)",
      }}
      id="main"
    >
      {/* Header */}
      <header
        className="glass"
        style={{ borderBottom: "1px solid rgba(245,230,200,0.4)" }}
      >
        <div className="mx-auto max-w-3xl flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <Link
              href="/"
              className="btn-ghost rounded-xl hidden sm:flex"
              aria-label="Home"
            >
              <ChevronLeftIcon />
            </Link>
            <h1
              className="text-base font-bold sm:text-lg"
              style={{ color: "var(--color-green-dark)" }}
            >
              National Leaderboard
            </h1>
          </div>
          <Link
            href="/chat"
            className="btn-ghost rounded-xl text-xs font-semibold hidden sm:flex"
            style={{ color: "var(--color-green)" }}
          >
            AI Coach
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-3xl px-4 py-6 space-y-6">
        {/* Loading skeleton */}
        {loading && <SkeletonLeaderboard />}

        {/* Error state */}
        {!loading && error && (
          <div className="card text-center p-8">
            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl" style={{ background: "rgba(239,68,68,0.08)" }}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-danger)" strokeWidth="2" strokeLinecap="round">
                <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <h2 className="text-lg font-bold mb-2" style={{ color: "var(--color-text)" }}>Could not load leaderboard</h2>
            <p className="text-sm mb-4" style={{ color: "var(--color-text-muted)" }}>Please check your connection and try again.</p>
            <button onClick={fetchData} className="btn-primary">Retry</button>
          </div>
        )}

        {!loading && !error && (
          <>
            {/* Impact Stats Banner */}
            <div
              className="card"
              style={{
                background:
                  "linear-gradient(135deg, var(--color-green-dark), var(--color-green))",
              }}
            >
              <div className="grid grid-cols-3 gap-2 sm:gap-4 text-center">
                <div>
                  <div className="text-2xl font-extrabold text-white">
                    {data?.total_entrepreneurs || "--"}
                  </div>
                  <div className="text-xs text-white/70">Entrepreneurs</div>
                </div>
                <div>
                  <div
                    className="text-2xl font-extrabold"
                    style={{ color: "var(--color-gold-light)" }}
                  >
                    {data?.total_businesses_launched || "--"}
                  </div>
                  <div className="text-xs text-white/70">Launched</div>
                </div>
                <div>
                  <div className="text-2xl font-extrabold text-white">
                    {data?.total_jobs_created || "--"}
                  </div>
                  <div className="text-xs text-white/70">Jobs Created</div>
                </div>
              </div>
              {data?.impact_note && (
                <p className="text-xs text-white/60 text-center mt-3">
                  {data.impact_note}
                </p>
              )}
            </div>

            {/* Tabs */}
            <div className="tab-bar">
              {(["leaderboard", "stories"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`tab-item ${tab === t ? "active" : ""}`}
                >
                  {t === "stories" ? "Success Stories" : "Leaderboard"}
                </button>
              ))}
            </div>

            {/* Leaderboard */}
            {tab === "leaderboard" && data?.entries && (
              <div className="space-y-3 animate-fade-in">
                {data.entries.map((e) => {
                  const badge =
                    BADGE_INFO[e.badge] || BADGE_INFO.rising_star;
                  const isCurrentUser =
                    isAuthenticated &&
                    userName &&
                    e.name.toLowerCase().startsWith(userName.split(" ")[0].toLowerCase());
                  return (
                    <div
                      key={e.rank}
                      className="card flex items-center gap-4 !p-3"
                      style={
                        isCurrentUser
                          ? {
                              border: "2px solid var(--color-gold)",
                              boxShadow:
                                "0 0 0 3px rgba(212,160,23,0.15), var(--shadow-glass)",
                            }
                          : undefined
                      }
                    >
                      <div
                        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-lg font-extrabold text-white"
                        style={{
                          background:
                            e.rank <= 3
                              ? "linear-gradient(135deg, var(--color-gold), var(--color-gold-dark))"
                              : "var(--color-green)",
                        }}
                      >
                        {e.rank}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span
                            className="font-bold text-sm"
                            style={{ color: "var(--color-text)" }}
                          >
                            {e.name}
                          </span>
                          <span className="text-lg" title={badge.label}>
                            {badge.emoji}
                          </span>
                          {isCurrentUser && (
                            <span
                              className="text-[10px] font-bold px-1.5 py-0.5 rounded-full"
                              style={{
                                background: "rgba(212,160,23,0.15)",
                                color: "var(--color-gold-dark)",
                              }}
                            >
                              You
                            </span>
                          )}
                        </div>
                        <div
                          className="text-xs"
                          style={{ color: "var(--color-text-muted)" }}
                        >
                          {e.business_type} — {e.location}
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <div
                          className="text-sm font-bold"
                          style={{ color: "var(--color-green)" }}
                        >
                          {e.milestones_completed} steps
                        </div>
                        <div
                          className="text-[10px]"
                          style={{
                            color:
                              STAGE_COLORS[e.stage] ||
                              "var(--color-text-muted)",
                          }}
                        >
                          {e.stage}
                        </div>
                      </div>
                    </div>
                  );
                })}

                <div className="text-center pt-4">
                  <Link
                    href="/auth"
                    className="btn-gold no-underline text-sm"
                  >
                    Join the Leaderboard
                  </Link>
                </div>
              </div>
            )}

            {/* Success Stories */}
            {tab === "stories" && (
              <div className="space-y-6 animate-fade-in">
                {/* Filter pills */}
                <div className="flex gap-2 overflow-x-auto pb-2 sm:flex-wrap sm:overflow-visible">
                  {STORY_CATEGORIES.map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setStoryFilter(cat)}
                      className="px-3 py-1.5 rounded-full text-xs font-semibold transition-all"
                      style={{
                        background:
                          storyFilter === cat
                            ? "var(--color-green)"
                            : "var(--color-glass)",
                        color:
                          storyFilter === cat
                            ? "white"
                            : "var(--color-text-muted)",
                        border:
                          storyFilter === cat
                            ? "1px solid var(--color-green)"
                            : "1px solid rgba(245,230,200,0.6)",
                      }}
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                {filteredStories.length === 0 && (
                  <div className="card text-center p-8">
                    <p
                      className="text-sm"
                      style={{ color: "var(--color-text-muted)" }}
                    >
                      No stories in this category yet.
                    </p>
                  </div>
                )}

                {filteredStories.map((s, i) => (
                  <div key={i} className="card">
                    <div className="flex items-center gap-3 mb-3">
                      <div
                        className="h-12 w-12 rounded-full flex items-center justify-center text-xl font-bold text-white"
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
                          {s.business} — {s.location}
                        </p>
                      </div>
                    </div>

                    <p
                      className="text-sm mb-4"
                      style={{
                        color: "var(--color-text)",
                        lineHeight: 1.7,
                      }}
                    >
                      {s.story}
                    </p>

                    <div className="grid grid-cols-1 gap-2 mb-4 sm:grid-cols-3 sm:gap-3">
                      <div
                        className="text-center p-2 rounded-lg"
                        style={{ background: "rgba(45,106,79,0.06)" }}
                      >
                        <div
                          className="text-sm font-bold"
                          style={{ color: "var(--color-green)" }}
                        >
                          {s.revenue}
                        </div>
                        <div
                          className="text-[10px]"
                          style={{ color: "var(--color-text-muted)" }}
                        >
                          Now Earning
                        </div>
                      </div>
                      <div
                        className="text-center p-2 rounded-lg"
                        style={{ background: "rgba(212,160,23,0.06)" }}
                      >
                        <div
                          className="text-sm font-bold"
                          style={{ color: "var(--color-gold-dark)" }}
                        >
                          {s.started_with}
                        </div>
                        <div
                          className="text-[10px]"
                          style={{ color: "var(--color-text-muted)" }}
                        >
                          Started With
                        </div>
                      </div>
                      <div
                        className="text-center p-2 rounded-lg"
                        style={{ background: "rgba(139,94,60,0.06)" }}
                      >
                        <div
                          className="text-sm font-bold"
                          style={{ color: "var(--color-earth)" }}
                        >
                          {s.time}
                        </div>
                        <div
                          className="text-[10px]"
                          style={{ color: "var(--color-text-muted)" }}
                        >
                          Time to Grow
                        </div>
                      </div>
                    </div>

                    <div
                      className="p-3 rounded-lg"
                      style={{
                        background: "rgba(45,106,79,0.04)",
                        borderLeft: "3px solid var(--color-green)",
                      }}
                    >
                      <p
                        className="text-xs font-bold mb-1"
                        style={{ color: "var(--color-green-dark)" }}
                      >
                        Key Lesson
                      </p>
                      <p
                        className="text-sm"
                        style={{ color: "var(--color-text)" }}
                      >
                        {s.key_lesson}
                      </p>
                    </div>
                  </div>
                ))}

                <div className="text-center">
                  <p
                    className="text-sm italic mb-4"
                    style={{ color: "var(--color-text-muted)" }}
                  >
                    These are real stories from Ugandan youth entrepreneurs.
                    Your story could be next.
                  </p>
                  <Link href="/chat" className="btn-primary no-underline">
                    Start Your Story
                  </Link>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
