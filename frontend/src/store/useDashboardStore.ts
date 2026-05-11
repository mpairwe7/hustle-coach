"use client";

import { create } from "zustand";
import type {
  BusinessProfile,
  DashboardData,
  DoctorResult,
  Milestone,
} from "@/lib/api";

interface DashboardState {
  data: DashboardData | null;
  doctor: DoctorResult | null;
  loading: boolean;
  doctorLoading: boolean;
  saveLoading: boolean;
  tab: "milestones" | "doctor" | "profile";
  profile: BusinessProfile;

  setData: (data: DashboardData) => void;
  setDoctor: (doctor: DoctorResult | null) => void;
  setLoading: (loading: boolean) => void;
  setDoctorLoading: (loading: boolean) => void;
  setSaveLoading: (loading: boolean) => void;
  setTab: (tab: "milestones" | "doctor" | "profile") => void;
  setProfile: (profile: BusinessProfile) => void;
  updateProfileField: (key: keyof BusinessProfile, value: string | number) => void;

  /** Optimistic milestone toggle with rollback support */
  toggleMilestone: (id: string, completed: boolean) => void;
  rollbackMilestone: (id: string, completed: boolean) => void;

  reset: () => void;
}

const DEFAULT_PROFILE: BusinessProfile = {
  business_name: "",
  business_type: "",
  location: "",
  startup_capital_ugx: 0,
  monthly_revenue_ugx: 0,
  monthly_profit_ugx: 0,
  employees: 0,
  stage: "idea",
};

function recalcHealth(milestones: Milestone[], total: number) {
  const completed = milestones.filter((m) => m.completed).length;
  return {
    completed_milestones: completed,
    health_score: Math.min(100, Math.floor((completed / Math.max(total, 1)) * 100)),
  };
}

export const useDashboardStore = create<DashboardState>()((set) => ({
  data: null,
  doctor: null,
  loading: true,
  doctorLoading: false,
  saveLoading: false,
  tab: "milestones",
  profile: DEFAULT_PROFILE,

  setData: (data) => set({ data, profile: data.profile, loading: false }),
  setDoctor: (doctor) => set({ doctor }),
  setLoading: (loading) => set({ loading }),
  setDoctorLoading: (doctorLoading) => set({ doctorLoading }),
  setSaveLoading: (saveLoading) => set({ saveLoading }),
  setTab: (tab) => set({ tab }),
  setProfile: (profile) => set({ profile }),

  updateProfileField: (key, value) =>
    set((state) => ({
      profile: { ...state.profile, [key]: value },
    })),

  toggleMilestone: (id, completed) =>
    set((state) => {
      if (!state.data) return {};
      const milestones = state.data.milestones.map((m) =>
        m.id === id ? { ...m, completed } : m,
      );
      const { completed_milestones, health_score } = recalcHealth(
        milestones,
        state.data.total_milestones,
      );
      return {
        data: { ...state.data, milestones, completed_milestones, health_score },
      };
    }),

  rollbackMilestone: (id, completed) =>
    set((state) => {
      if (!state.data) return {};
      const milestones = state.data.milestones.map((m) =>
        m.id === id ? { ...m, completed: !completed } : m,
      );
      const { completed_milestones, health_score } = recalcHealth(
        milestones,
        state.data.total_milestones,
      );
      return {
        data: { ...state.data, milestones, completed_milestones, health_score },
      };
    }),

  reset: () =>
    set({
      data: null,
      doctor: null,
      loading: true,
      doctorLoading: false,
      saveLoading: false,
      tab: "milestones",
      profile: DEFAULT_PROFILE,
    }),
}));
