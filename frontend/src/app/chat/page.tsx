"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useChatStore } from "@/store/useChatStore";
import { useAuthStore } from "@/store/useAuthStore";
import { useTTS } from "@/hooks/useSpeech";
import { chatApi } from "@/lib/api";
import type { StreamChunk } from "@/lib/api";
import { ChatInput } from "@/components/ChatInput";
import { ChatMessage } from "@/components/ChatMessage";
import { StarterPrompts } from "@/components/StarterPrompts";
import { BusinessPlanCard } from "@/components/BusinessPlanCard";
import { DomainNav } from "@/components/DomainNav";
import { OfflineIndicator } from "@/components/OfflineIndicator";
import VoiceModal from "@/components/VoiceModal";
import { ChevronLeftIcon, ClearIcon } from "@/components/Icons";

const LOCALES = [
  { code: "en", label: "EN" },
  { code: "lg", label: "LG" },
  { code: "sw", label: "SW" },
  { code: "nyn", label: "NY" },
];

const PAGE_I18N: Record<string, {
  disclaimer: string; continueChat: string; thinking: string;
  newChat: string; clearBody: string; cancel: string; clearBtn: string;
  streamFallback: string;
}> = {
  en: { disclaimer: "AI advice is not a guarantee — always seek local mentors", continueChat: "Continue the conversation:", thinking: "Thinking...", newChat: "Start new conversation?", clearBody: "This will start a fresh chat. Your current conversation will be saved in the sidebar history.", cancel: "Cancel", clearBtn: "New chat", streamFallback: "Streaming unavailable — switched to standard response" },
  lg: { disclaimer: "Amagezi ga AI tegakakasiddwa — bulijjo noonya abakuyamba", continueChat: "Weyongere n'emboozi:", thinking: "Ndalowoza...", newChat: "Tandika emboozi empya?", clearBody: "Kino kijja kutandika emboozi empya. Emboozi ey'emabega ejja kukuumibwa mu history.", cancel: "Sazaamu", clearBtn: "Emboozi empya", streamFallback: "Okusindika tekulinnya — tukyuse ku ngeri eya bulijjo" },
  sw: { disclaimer: "Ushauri wa AI si dhamana — daima tafuta washauri wa karibu", continueChat: "Endelea na mazungumzo:", thinking: "Inafikiria...", newChat: "Anza mazungumzo mapya?", clearBody: "Hii itaanza mazungumzo mapya. Mazungumzo yako ya sasa yatahifadhiwa kwenye historia.", cancel: "Ghairi", clearBtn: "Mazungumzo mapya", streamFallback: "Utumaji wa moja kwa moja haupatikani — imebadilishwa kuwa jibu la kawaida" },
  nyn: { disclaimer: "Amagezi ga AI tiga kuteberera — buriijo noonye abakuyamba", continueChat: "Weyongere n'emboozi:", thinking: "Nindowooza...", newChat: "Tandika emboozi empya?", clearBody: "Kinu nikija kutandika emboozi empya. Emboozi ey'emabega ejja kukuumibwa mu history.", cancel: "Sazaho", clearBtn: "Emboozi empya", streamFallback: "Okusindika tikurikora — tukyuse ku ngeri eya buriijo" },
};

export default function ChatPage() {
  const messages = useChatStore((s) => s.messages);
  const locale = useChatStore((s) => s.locale);
  const sessionId = useChatStore((s) => s.sessionId);
  const isLoading = useChatStore((s) => s.isLoading);
  const addMessage = useChatStore((s) => s.addMessage);
  const updateLastAssistant = useChatStore((s) => s.updateLastAssistant);
  const setLoading = useChatStore((s) => s.setLoading);
  const setLocale = useChatStore((s) => s.setLocale);
  const clearChat = useChatStore((s) => s.clearChat);
  const createNewSession = useChatStore((s) => s.createNewSession);
  const sessions = useChatStore((s) => s.sessions);
  const switchSession = useChatStore((s) => s.switchSession);
  const deleteSession = useChatStore((s) => s.deleteSession);
  const sidebarOpen = useChatStore((s) => s.sidebarOpen);
  const setSidebarOpen = useChatStore((s) => s.setSidebarOpen);
  const activeSessionId = useChatStore((s) => s.activeSessionId);

  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const tts = useTTS(locale);
  const pt = PAGE_I18N[locale] || PAGE_I18N.en;

  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [toolProgress, setToolProgress] = useState<string | null>(null);
  const [collapsedMsgs, setCollapsedMsgs] = useState<Set<string>>(new Set());
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const [inputPrefill, setInputPrefill] = useState("");
  const [streamFallback, setStreamFallback] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const shouldAutoScrollRef = useRef(true);
  const dialogRef = useRef<HTMLDivElement>(null);

  // ─── Smart auto-scroll (Grok-style threshold) ───
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    if (shouldAutoScrollRef.current) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, [messages, toolProgress]);

  // ─── Scroll event: toggle auto-scroll + show/hide button ───
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const fn = () => {
      const dist = el.scrollHeight - el.scrollTop - el.clientHeight;
      shouldAutoScrollRef.current = dist < 120;
      setShowScrollBtn(dist > 220);
    };
    el.addEventListener("scroll", fn, { passive: true });
    return () => el.removeEventListener("scroll", fn);
  }, []);

  const scrollToBottom = () => {
    shouldAutoScrollRef.current = true;
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  };

  const toggleCollapse = useCallback((id: string) => {
    setCollapsedMsgs((p) => {
      const n = new Set(p);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });
  }, []);

  // ─── Send message with streaming ───
  const sendMessage = useCallback(
    async (text: string) => {
      if (isLoading) return;
      shouldAutoScrollRef.current = true;
      addMessage({ role: "user", content: text });
      setLoading(true);
      setToolProgress(null);
      addMessage({ role: "assistant", content: "", domain: "thinking" });
      abortRef.current = new AbortController();

      try {
        const res = await chatApi.stream(
          text,
          locale,
          sessionId,
          abortRef.current.signal,
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const reader = res.body?.getReader();
        if (!reader) throw new Error("No reader");
        const decoder = new TextDecoder();
        let fullText = "",
          buffer = "";
        let rafId: number | null = null;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const c: StreamChunk = JSON.parse(line.slice(6));
              if (c.tool_progress) {
                setToolProgress(c.tool_progress);
              } else if (c.done) {
                setToolProgress(null);
                if (rafId !== null) cancelAnimationFrame(rafId);
                const s = useChatStore.getState(),
                  msgs = [...s.messages],
                  last = msgs[msgs.length - 1];
                if (last?.role === "assistant") {
                  msgs[msgs.length - 1] = {
                    ...last,
                    content: fullText,
                    citations: c.citations || [],
                    faithfulness: c.faithfulness || 0,
                    domain: c.domain || "general",
                    confidence: c.confidence || "medium",
                    disclaimer: c.disclaimer || "",
                    businessPlan: c.business_plan || undefined,
                    toolCalls: c.tool_calls || [],
                    followUps: c.follow_ups || [],
                  };
                  useChatStore.setState({ messages: msgs });
                }
              } else if (c.token) {
                fullText += c.token;
                // RAF batching — update DOM at most once per frame
                if (rafId === null) {
                  rafId = requestAnimationFrame(() => {
                    updateLastAssistant(fullText);
                    rafId = null;
                  });
                }
              }
            } catch {
              /* ignore partial chunk parse errors */
            }
          }
        }
        // Flush any pending RAF
        if (rafId !== null) {
          cancelAnimationFrame(rafId);
          updateLastAssistant(fullText);
        }
      } catch (error) {
        if ((error as Error).name === "AbortError") return;
        setToolProgress(null);
        setStreamFallback(true);
        setTimeout(() => setStreamFallback(false), 3000);
        try {
          const d = await chatApi.send(text, locale, sessionId);
          const s = useChatStore.getState(),
            msgs = [...s.messages],
            last = msgs[msgs.length - 1];
          if (last?.role === "assistant") {
            msgs[msgs.length - 1] = {
              ...last,
              content: d.answer,
              citations: d.citations || [],
              faithfulness: d.faithfulness || 0,
              domain: d.domain || "general",
              confidence: d.confidence || "medium",
              disclaimer: d.disclaimer || "",
              businessPlan: d.business_plan || undefined,
              toolCalls: d.tool_calls || [],
              followUps: d.follow_ups || [],
            };
            useChatStore.setState({ messages: msgs });
          }
        } catch {
          updateLastAssistant(
            "I'm having trouble connecting. Please check your internet and try again.",
          );
        }
      } finally {
        setLoading(false);
        setToolProgress(null);
        abortRef.current = null;
      }
    },
    [isLoading, locale, sessionId, addMessage, updateLastAssistant, setLoading],
  );

  const handleDomainSelect = useCallback((prompt: string) => {
    setInputPrefill(prompt);
    // Clear prefill after a tick so it can be re-triggered with same value
    setTimeout(() => setInputPrefill(""), 0);
  }, []);

  const handleClearChat = () => {
    // Save current chat to session history, then start fresh
    createNewSession();
    setShowClearConfirm(false);
    setCollapsedMsgs(new Set());
  };

  /** Trap Tab focus within the clear-chat confirmation dialog */
  const handleDialogKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Escape") {
        setShowClearConfirm(false);
        return;
      }
      if (e.key !== "Tab") return;
      const dialog = dialogRef.current;
      if (!dialog) return;
      const focusable = dialog.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    },
    [],
  );

  const hasMessages = messages.length > 0;
  const lastMsg = messages[messages.length - 1];

  return (
    <div
      className="flex h-dvh flex-col"
      style={{
        background:
          "linear-gradient(180deg, var(--color-cream) 0%, #F5ECD7 100%)",
      }}
    >
      <OfflineIndicator />

      {/* ═══ SESSION SIDEBAR ═══ */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40"
          style={{ background: "rgba(0,0,0,0.4)" }}
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <aside
        className="fixed top-0 left-0 z-50 flex h-dvh flex-col transition-transform duration-300"
        style={{
          width: "min(300px, 85vw)",
          background: "var(--color-cream, #fdf6e3)",
          borderRight: "1px solid rgba(245,230,200,0.5)",
          transform: sidebarOpen ? "translateX(0)" : "translateX(-100%)",
          boxShadow: sidebarOpen ? "4px 0 24px rgba(0,0,0,0.15)" : "none",
        }}
      >
        <div className="flex items-center justify-between p-3 border-b" style={{ borderColor: "rgba(245,230,200,0.5)" }}>
          <h2 className="text-sm font-bold" style={{ color: "var(--color-green-dark, #1b4332)" }}>Conversations</h2>
          <button onClick={() => setSidebarOpen(false)} className="text-xl" style={{ color: "var(--color-text-muted)" }}>&times;</button>
        </div>
        <button
          onClick={() => { createNewSession(); setSidebarOpen(false); }}
          className="mx-3 mt-3 flex items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-semibold text-white"
          style={{ background: "linear-gradient(135deg, var(--color-green, #2d6a4f), var(--color-green-dark, #1b4332))" }}
        >
          + New Chat
        </button>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.length === 0 && (
            <p className="text-center text-xs py-8" style={{ color: "var(--color-text-light)" }}>No conversations yet</p>
          )}
          {[...sessions].sort((a, b) => b.updatedAt - a.updatedAt).map((sess) => (
            <div
              key={sess.id}
              onClick={() => { switchSession(sess.id); setSidebarOpen(false); }}
              className="flex items-center justify-between rounded-lg px-3 py-2.5 cursor-pointer transition-colors"
              style={{
                background: sess.id === activeSessionId ? "rgba(45,106,79,0.1)" : "transparent",
                borderLeft: sess.id === activeSessionId ? "3px solid var(--color-green)" : "3px solid transparent",
              }}
            >
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium truncate" style={{ color: "var(--color-text)" }}>{sess.title || "New Chat"}</p>
                <p className="text-[10px]" style={{ color: "var(--color-text-light)" }}>
                  {new Date(sess.updatedAt).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                  {sess.domain !== "general" && ` · ${sess.domain}`}
                </p>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); deleteSession(sess.id); }}
                className="ml-2 text-sm opacity-0 hover:opacity-100 transition-opacity"
                style={{ color: "var(--color-danger, #ef4444)" }}
                aria-label="Delete"
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* ═══ HEADER ═══ */}
      <header
        className="glass"
        style={{
          borderBottom: "1px solid rgba(245,230,200,0.4)",
          flexShrink: 0,
          zIndex: 10,
        }}
      >
        <div className="chat-content-lane flex items-center justify-between px-2 py-1.5 sm:px-4 sm:py-2 md:px-5">
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Sidebar toggle */}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="btn-ghost rounded-xl flex items-center justify-center"
              style={{ width: 36, height: 36 }}
              aria-label="Conversations"
              type="button"
            >
              <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path d="M3 12h18M3 6h18M3 18h18" />
              </svg>
            </button>
            <div className="flex items-center gap-2">
              <div
                className="flex h-8 w-8 items-center justify-center rounded-lg sm:h-9 sm:w-9"
                style={{
                  background:
                    "linear-gradient(135deg, var(--color-green), var(--color-green-dark))",
                }}
              >
                <svg
                  width="18"
                  height="18"
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
              <div>
                <h1
                  className="text-sm font-bold leading-tight sm:text-base"
                  style={{ color: "var(--color-green-dark)" }}
                >
                  HustleScale
                </h1>
                <p
                  className="hidden text-[11px] leading-tight sm:block"
                  style={{ color: "var(--color-text-light)" }}
                >
                  National Youth Accelerator
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1 sm:gap-1.5">
            <div
              className="flex rounded-lg overflow-hidden"
              style={{ border: "1px solid rgba(245,230,200,0.6)" }}
            >
              {LOCALES.map((l) => (
                <button
                  key={l.code}
                  onClick={() => setLocale(l.code as "en" | "lg" | "nyn" | "sw")}
                  className="px-2 py-1.5 text-[11px] font-semibold transition-all sm:px-2.5 sm:text-xs"
                  style={{
                    background:
                      locale === l.code ? "var(--color-green)" : "transparent",
                    color:
                      locale === l.code ? "white" : "var(--color-text-muted)",
                    minHeight: "44px",
                  }}
                  aria-label={`Switch to ${l.label}`}
                >
                  {l.label}
                </button>
              ))}
            </div>
            {!isAuthenticated && (
              <Link
                href="/auth"
                className="btn-ghost rounded-xl text-[11px] font-semibold sm:text-xs"
                style={{ color: "var(--color-green)" }}
              >
                Sign in
              </Link>
            )}
            {hasMessages && (
              <button
                onClick={() => setShowClearConfirm(true)}
                className="btn-ghost rounded-xl"
                aria-label="New chat"
                title="New conversation"
              >
                <ClearIcon />
              </button>
            )}
          </div>
        </div>
      </header>

      {/* ═══ MESSAGES — edge-masked scrolling ═══ */}
      <div
        ref={scrollRef}
        className="chat-scroll-area"
        id="main"
        role="log"
        aria-live="polite"
      >
        <div className="chat-content-lane px-2 py-3 sm:px-4 sm:py-4 md:px-5 md:py-5 lg:px-6">
          {!hasMessages ? (
            <StarterPrompts onSelect={sendMessage} />
          ) : (
            <div className="space-y-2">
              {messages.map((msg, idx) => (
                <div key={msg.id}>
                  <ChatMessage
                    message={msg}
                    onListen={tts.play}
                    playingId={tts.playingId}
                    collapsed={collapsedMsgs.has(msg.id)}
                    onToggleCollapse={() => toggleCollapse(msg.id)}
                    locale={locale}
                  />

                  {/* Business plan card */}
                  {msg.role === "assistant" &&
                  msg.businessPlan?.startup_budget?.length ? (
                    <div className="mt-3 ml-[36px] sm:ml-[42px] md:ml-[54px] animate-slide-in">
                      <BusinessPlanCard plan={msg.businessPlan} />
                    </div>
                  ) : null}

                  {/* Follow-up suggestions */}
                  {msg.role === "assistant" &&
                  idx === messages.length - 1 &&
                  msg.followUps?.length &&
                  !isLoading ? (
                    <div className="mt-3 ml-[36px] sm:ml-[42px] md:ml-[54px] space-y-1.5 animate-slide-in">
                      <p
                        className="text-[11px] font-medium"
                        style={{ color: "var(--color-text-light)" }}
                      >
                        {pt.continueChat}
                      </p>
                      <div className="flex flex-col gap-1.5 sm:flex-row sm:flex-wrap">
                        {msg.followUps.map((q, i) => (
                          <button
                            key={i}
                            onClick={() => sendMessage(q)}
                            className="follow-up-chip text-left"
                          >
                            <span className="follow-up-arrow">&#x2192;</span>
                            {q}
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              ))}

              {/* Tool progress indicator */}
              {toolProgress && (
                <div className="ml-[36px] sm:ml-[42px] md:ml-[54px]">
                  <div className="tool-progress animate-slide-in">
                    <div className="dot" />
                    <span>{toolProgress}...</span>
                  </div>
                </div>
              )}

              {/* Thinking indicator */}
              {isLoading &&
                !toolProgress &&
                lastMsg?.role === "assistant" &&
                !lastMsg?.content && (
                  <article className="message-row message-row-assistant">
                    <div className="avatar avatar-assistant" aria-hidden="true">
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                      >
                        <path d="M12 3v18M3 12l3-3 3 3M15 12l3-3 3 3M6 9v9a3 3 0 003 3h6a3 3 0 003-3V9" />
                      </svg>
                    </div>
                    <div className="bubble bubble-assistant">
                      <span className="bubble-role">HustleScale</span>
                      <div className="flex items-center gap-3">
                        <div className="typing-dots">
                          <span />
                          <span />
                          <span />
                        </div>
                        <span
                          className="text-sm"
                          style={{ color: "var(--color-text-muted)" }}
                        >
                          {pt.thinking}
                        </span>
                      </div>
                    </div>
                  </article>
                )}
            </div>
          )}
        </div>

        {/* Scroll-to-bottom button */}
        {showScrollBtn && (
          <button
            onClick={scrollToBottom}
            className="scroll-bottom-btn"
            aria-label="Scroll to bottom"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 5v14M5 12l7 7 7-7" />
            </svg>
          </button>
        )}
      </div>

      {/* ═══ INPUT BAR ═══ */}
      <div
        className="chat-input-bar glass"
        style={{
          borderTop: "1px solid rgba(245,230,200,0.4)",
          flexShrink: 0,
        }}
      >
        <div className="chat-content-lane space-y-1.5 sm:space-y-2">
          {/* TTS error */}
          {tts.error && (
            <div
              className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs"
              style={{ background: "rgba(212,160,23,0.08)", color: "var(--color-gold-dark)" }}
              role="alert"
            >
              <span className="flex-1">{tts.error}</span>
              <button onClick={tts.clearError} className="font-semibold underline" style={{ color: "var(--color-gold-dark)" }}>
                Dismiss
              </button>
            </div>
          )}
          {streamFallback && (
            <div
              className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs animate-fade-in"
              style={{ background: "rgba(45,106,79,0.08)", color: "var(--color-green)" }}
              role="status"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span className="flex-1">{pt.streamFallback}</span>
            </div>
          )}
          {hasMessages && <DomainNav onSelect={handleDomainSelect} />}
          <ChatInput onSend={sendMessage} disabled={isLoading} locale={locale} prefill={inputPrefill} />
          <p
            className="text-center text-[10px] sm:text-[11px]"
            style={{ color: "var(--color-text-light)" }}
          >
            {pt.disclaimer}
          </p>
        </div>
      </div>

      {/* ═══ CLEAR DIALOG ═══ */}
      {showClearConfirm && (
        <div
          className="confirm-overlay"
          onClick={() => setShowClearConfirm(false)}
          onKeyDown={handleDialogKeyDown}
          role="dialog"
          aria-modal="true"
          aria-label={pt.newChat}
        >
          <div
            ref={dialogRef}
            className="confirm-dialog"
            onClick={(e) => e.stopPropagation()}
          >
            <h3
              className="text-lg font-bold mb-2"
              style={{ color: "var(--color-text)" }}
            >
              {pt.newChat}
            </h3>
            <p
              className="text-sm mb-5"
              style={{ color: "var(--color-text-muted)" }}
            >
              {pt.clearBody}
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowClearConfirm(false)}
                className="btn-outline flex-1 !py-2.5 !text-sm"
              >
                {pt.cancel}
              </button>
              <button
                onClick={handleClearChat}
                className="btn-primary flex-1 !py-2.5 !text-sm"
                style={{
                  background: "var(--color-danger)",
                  boxShadow: "0 4px 16px rgba(239,68,68,0.2)",
                }}
              >
                {pt.clearBtn}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Voice modal (Sunbird STT) */}
      <VoiceModal />
    </div>
  );
}
