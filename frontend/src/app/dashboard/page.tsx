"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronLeftIcon } from "@/components/Icons";
import {
  DashboardLoadingShell,
  DashboardErrorShell,
  DashboardAuthShell,
} from "@/components/dashboard/DashboardShells";
import { StatsOverview } from "@/components/dashboard/StatsOverview";
import { MilestoneList } from "@/components/dashboard/MilestoneList";
import { BusinessDoctor } from "@/components/dashboard/BusinessDoctor";
import { ProfileEditor } from "@/components/dashboard/ProfileEditor";
import { useAuthStore } from "@/store/useAuthStore";
import { useDashboardStore } from "@/store/useDashboardStore";
import { dashboardApi, doctorApi } from "@/lib/api";

const STAGE_LABELS: Record<string, { label: string; color: string }> = {
  idea: { label: "Idea Stage", color: "var(--color-text-muted)" },
  planning: { label: "Planning", color: "var(--color-gold)" },
  registered: { label: "Registered", color: "var(--color-earth)" },
  launched: { label: "Launched", color: "var(--color-green-light)" },
  growing: { label: "Growing", color: "var(--color-green)" },
  scaling: { label: "Scaling", color: "var(--color-green-dark)" },
};

export default function DashboardPage() {
  const router = useRouter();
  const token = useAuthStore((s) => s.token);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const logout = useAuthStore((s) => s.logout);

  const {
    data,
    doctor,
    loading,
    doctorLoading,
    saveLoading,
    tab,
    profile,
    setData,
    setDoctor,
    setLoading,
    setDoctorLoading,
    setSaveLoading,
    setTab,
    updateProfileField,
    toggleMilestone,
    rollbackMilestone,
  } = useDashboardStore();

  const [saveSuccess, setSaveSuccess] = useState(false);
  const [fetchError, setFetchError] = useState(false);

  const fetchDashboard = useCallback(() => {
    setFetchError(false);
    setLoading(true);
    dashboardApi
      .get()
      .then(setData)
      .catch(() => setFetchError(true))
      .finally(() => setLoading(false));
  }, [setData, setLoading]);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    fetchDashboard();
  }, [token, fetchDashboard, setLoading]);

  const handleToggleMilestone = useCallback(
    async (id: string, completed: boolean) => {
      if (!token) return;
      toggleMilestone(id, completed);
      try {
        await dashboardApi.updateMilestone(id, completed);
      } catch {
        rollbackMilestone(id, completed);
      }
    },
    [token, toggleMilestone, rollbackMilestone],
  );

  const runDoctorCheckup = useCallback(async () => {
    setDoctorLoading(true);
    try {
      const result = await doctorApi.checkup({
        business_type: profile.business_type || "general",
        monthly_revenue_ugx: Math.max(0, profile.monthly_revenue_ugx),
        monthly_costs_ugx: Math.max(
          0,
          profile.monthly_revenue_ugx - profile.monthly_profit_ugx,
        ),
        months_operating: 0,
        employees: Math.max(0, profile.employees),
        location: profile.location,
      });
      setDoctor(result);
    } catch {
      setDoctor(null);
    } finally {
      setDoctorLoading(false);
    }
  }, [profile, setDoctor, setDoctorLoading]);

  const saveProfile = useCallback(async () => {
    if (!token) return;
    setSaveLoading(true);
    setSaveSuccess(false);
    try {
      await dashboardApi.updateProfile(profile);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch {
      /* silent */
    } finally {
      setSaveLoading(false);
    }
  }, [token, profile, setSaveLoading]);

  if (loading) return <DashboardLoadingShell />;
  if (fetchError && isAuthenticated) return <DashboardErrorShell onRetry={fetchDashboard} />;
  if (!isAuthenticated || !token) return <DashboardAuthShell />;

  const stageInfo =
    STAGE_LABELS[data?.profile.stage || "idea"] || STAGE_LABELS.idea;

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
              My Dashboard
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <span
              className="badge text-[10px]"
              style={{
                background: `${stageInfo.color}20`,
                color: stageInfo.color,
              }}
            >
              {stageInfo.label}
            </span>
            <Link
              href="/chat"
              className="btn-ghost rounded-xl text-xs font-semibold hidden sm:flex"
              style={{ color: "var(--color-green)" }}
            >
              AI Coach
            </Link>
            <button
              onClick={() => { logout(); router.push("/"); }}
              className="btn-ghost rounded-xl text-xs font-semibold"
              style={{ color: "var(--color-danger)" }}
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-3xl px-4 py-6 space-y-6">
        <StatsOverview
          healthScore={data?.health_score || 0}
          completedMilestones={data?.completed_milestones || 0}
          totalMilestones={data?.total_milestones || 0}
          profile={profile}
        />

        {/* Tabs */}
        <div className="tab-bar" role="tablist">
          {(["milestones", "doctor", "profile"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`tab-item ${tab === t ? "active" : ""}`}
              role="tab"
              aria-selected={tab === t}
            >
              {t === "doctor" ? "Business Doctor" : t}
            </button>
          ))}
        </div>

        {tab === "milestones" && (
          <MilestoneList
            milestones={data?.milestones || []}
            onToggle={handleToggleMilestone}
            recommendations={data?.recommendations}
          />
        )}

        {tab === "doctor" && (
          <BusinessDoctor
            doctor={doctor}
            loading={doctorLoading}
            onRun={runDoctorCheckup}
          />
        )}

        {tab === "profile" && (
          <ProfileEditor
            profile={profile}
            onUpdate={updateProfileField}
            onSave={saveProfile}
            saving={saveLoading}
            saveSuccess={saveSuccess}
          />
        )}
      </div>
    </div>
  );
}
