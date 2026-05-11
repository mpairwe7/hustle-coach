"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  token: string | null;
  userId: string | null;
  userName: string | null;
  credits: number;
  isAuthenticated: boolean;

  login: (token: string, userId: string, name?: string, credits?: number) => void;
  logout: () => void;
  updateCredits: (credits: number) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      userId: null,
      userName: null,
      credits: 0,
      isAuthenticated: false,

      login: (token, userId, name, credits) => {
        // Single source: write to both Zustand-persisted state AND legacy keys
        // so api.ts can read from localStorage directly (avoids hydration issues)
        if (typeof window !== "undefined") {
          localStorage.setItem("hustle-scale-token", token);
          localStorage.setItem("hustle-scale-user-id", userId);
        }
        set({
          token,
          userId,
          userName: name || null,
          credits: credits || 0,
          isAuthenticated: true,
        });
      },

      logout: () => {
        // Clear ALL token storage
        if (typeof window !== "undefined") {
          localStorage.removeItem("hustle-scale-token");
          localStorage.removeItem("hustle-scale-user-id");
          localStorage.removeItem("hustle-coach-token");
        }
        set({
          token: null,
          userId: null,
          userName: null,
          credits: 0,
          isAuthenticated: false,
        });
      },

      updateCredits: (credits) => set({ credits }),
    }),
    {
      name: "hustle-scale-auth",
      partialize: (state) => ({
        token: state.token,
        userId: state.userId,
        userName: state.userName,
        credits: state.credits,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
