"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type {
  Citation,
  BusinessPlan,
  ToolCallRecord,
} from "@/lib/api";

// Re-export for consumers that import from this file
export type { Citation, BusinessPlan, ToolCallRecord };

export type Locale = "en" | "lg" | "nyn" | "sw";
export type SpeechState = "idle" | "listening" | "unavailable" | "error";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  citations?: Citation[];
  faithfulness?: number;
  domain?: string;
  confidence?: string;
  disclaimer?: string;
  locale?: string;
  businessPlan?: BusinessPlan;
  toolCalls?: ToolCallRecord[];
  followUps?: string[];
}

export interface Session {
  id: string;
  title: string;
  domain: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

interface ChatState {
  messages: ChatMessage[];
  locale: Locale;
  sessionId: string;
  isLoading: boolean;

  // Multi-session management
  sessions: Session[];
  activeSessionId: string | null;
  sidebarOpen: boolean;

  // Voice state
  speechState: SpeechState;
  voiceModalOpen: boolean;
  ttsEnabled: boolean;

  // Actions
  addMessage: (msg: Omit<ChatMessage, "id" | "timestamp">) => void;
  updateLastAssistant: (content: string) => void;
  setLoading: (loading: boolean) => void;
  setLocale: (locale: Locale) => void;
  clearChat: () => void;

  // Session actions
  createNewSession: () => void;
  switchSession: (id: string) => void;
  deleteSession: (id: string) => void;
  setSidebarOpen: (open: boolean) => void;

  // Voice actions
  setSpeechState: (state: SpeechState) => void;
  setVoiceModalOpen: (open: boolean) => void;
  setTtsEnabled: (enabled: boolean) => void;
}

const MAX_MESSAGES = 200;
const MAX_SESSIONS = 50;

const generateId = () =>
  `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: [],
      locale: "en" as Locale,
      sessionId: generateId(),
      isLoading: false,
      sessions: [],
      activeSessionId: null,
      sidebarOpen: false,
      speechState: "idle" as SpeechState,
      voiceModalOpen: false,
      ttsEnabled: true,

      addMessage: (msg) =>
        set((state) => {
          const newMsg = { ...msg, id: generateId(), timestamp: Date.now() };
          const messages = [...state.messages, newMsg].slice(-MAX_MESSAGES);

          // Auto-create session on first user message
          let sessions = [...state.sessions];
          let activeId = state.activeSessionId;
          if (!activeId) {
            const id = `s-${generateId()}`;
            const title = msg.role === "user" ? msg.content.slice(0, 60) : "New Chat";
            sessions = [
              { id, title, domain: msg.domain || "general", messages, createdAt: Date.now(), updatedAt: Date.now() },
              ...sessions,
            ].slice(0, MAX_SESSIONS);
            activeId = id;
          } else {
            sessions = sessions.map((s) =>
              s.id === activeId
                ? {
                    ...s,
                    messages,
                    updatedAt: Date.now(),
                    title: s.title === "New Chat" && msg.role === "user" ? msg.content.slice(0, 60) : s.title,
                  }
                : s
            );
          }
          return { messages, sessions, activeSessionId: activeId };
        }),

      updateLastAssistant: (content) =>
        set((state) => {
          const messages = [...state.messages];
          const last = messages[messages.length - 1];
          if (last && last.role === "assistant") {
            messages[messages.length - 1] = { ...last, content };
          }
          return { messages };
        }),

      setLoading: (isLoading) => set({ isLoading }),
      setLocale: (locale) => set({ locale }),
      clearChat: () =>
        set({ messages: [], sessionId: generateId(), activeSessionId: null }),

      // Session management
      createNewSession: () =>
        set((state) => {
          // Save current chat to active session before creating new
          let sessions = state.activeSessionId
            ? state.sessions.map((s) =>
                s.id === state.activeSessionId ? { ...s, messages: state.messages, updatedAt: Date.now() } : s
              )
            : state.sessions;
          if (state.messages.length === 0 && state.activeSessionId) {
            sessions = sessions.filter((s) => s.id !== state.activeSessionId);
          }
          return { messages: [], sessions, activeSessionId: null, sessionId: generateId() };
        }),

      switchSession: (id) =>
        set((state) => {
          const target = state.sessions.find((s) => s.id === id);
          if (!target) return state;
          let sessions = state.activeSessionId
            ? state.sessions.map((s) =>
                s.id === state.activeSessionId ? { ...s, messages: state.messages, updatedAt: Date.now() } : s
              )
            : state.sessions;
          return { messages: target.messages, sessions, activeSessionId: id, sidebarOpen: false };
        }),

      deleteSession: (id) =>
        set((state) => {
          const sessions = state.sessions.filter((s) => s.id !== id);
          if (state.activeSessionId === id) {
            const next = sessions[0];
            return { sessions, messages: next ? next.messages : [], activeSessionId: next ? next.id : null };
          }
          return { sessions };
        }),

      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),

      // Voice
      setSpeechState: (speechState) => set({ speechState }),
      setVoiceModalOpen: (voiceModalOpen) => set({ voiceModalOpen }),
      setTtsEnabled: (ttsEnabled) => set({ ttsEnabled }),
    }),
    {
      name: "hustle-scale-chat",
      storage: createJSONStorage(() =>
        typeof window !== "undefined"
          ? localStorage
          : ({ getItem: () => null, setItem: () => {}, removeItem: () => {} } as unknown as Storage)
      ),
      partialize: (state) => ({
        messages: state.messages,
        locale: state.locale,
        sessionId: state.sessionId,
        sessions: state.sessions,
        activeSessionId: state.activeSessionId,
        ttsEnabled: state.ttsEnabled,
      }),
    },
  ),
);
