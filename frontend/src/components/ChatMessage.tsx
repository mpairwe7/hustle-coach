"use client";

import { memo, useState, useCallback } from "react";
import type { ChatMessage as ChatMessageType } from "@/store/useChatStore";
import { Markdown } from "./Markdown";
import { feedbackApi } from "@/lib/api";

const COLLAPSE_THRESHOLD = 800;

const MSG_I18N: Record<string, {
  you: string; copy: string; copied: string; listen: string; stop: string;
  expand: string; collapse: string; helpful: string; notHelpful: string;
  sources: string; grounded: string; verify: string; medium: string;
}> = {
  en: { you: "You", copy: "Copy", copied: "Copied", listen: "Listen", stop: "Stop", expand: "Expand", collapse: "Collapse", helpful: "Helpful", notHelpful: "Not helpful", sources: "Sources", grounded: "Grounded", verify: "Verify", medium: "Medium" },
  lg: { you: "Ggwe", copy: "Koppa", copied: "Ekoppeddwa", listen: "Wuliriza", stop: "Komya", expand: "Yanjuluza", collapse: "Funya", helpful: "Kiyambye", notHelpful: "Tekiyambye", sources: "Ensibuko", grounded: "Kakasiddwa", verify: "Kakasa", medium: "Wakati" },
  sw: { you: "Wewe", copy: "Nakili", copied: "Imenakiliwa", listen: "Sikiliza", stop: "Simama", expand: "Panua", collapse: "Kunja", helpful: "Inasaidia", notHelpful: "Haisaidii", sources: "Vyanzo", grounded: "Imethibitishwa", verify: "Thibitisha", medium: "Wastani" },
  nyn: { you: "Iwe", copy: "Koppa", copied: "Ekoppeddwa", listen: "Huurira", stop: "Hagarika", expand: "Yanjura", collapse: "Funya", helpful: "Kiyambire", notHelpful: "Tekiyambire", sources: "Ensibuko", grounded: "Kakasirwe", verify: "Kakasa", medium: "Ahakati" },
};

interface Props {
  message: ChatMessageType;
  /** Called with (turnId, text) to play/stop TTS */
  onListen?: (turnId: string, text: string) => void;
  /** ID of the message currently being spoken */
  playingId?: string | null;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  locale?: string;
}

export const ChatMessage = memo(
  function ChatMessage({
    message,
    onListen,
    playingId,
    collapsed,
    onToggleCollapse,
    locale = "en",
  }: Props) {
    const isUser = message.role === "user";
    const isLong = message.content.length > COLLAPSE_THRESHOLD;
    const [copied, setCopied] = useState(false);
    const [feedback, setFeedback] = useState<"up" | "down" | null>(null);
    const t = MSG_I18N[locale] || MSG_I18N.en;

    const handleCopy = useCallback(async () => {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }, [message.content]);

    const isPlaying = playingId === message.id;

    const handleListen = useCallback(() => {
      onListen?.(message.id, message.content);
    }, [onListen, message.id, message.content]);

    const handleFeedback = useCallback(
      (type: "up" | "down") => {
        const next = feedback === type ? null : type;
        setFeedback(next);
        if (next) {
          feedbackApi
            .submit(message.id, next === "up" ? 1 : -1)
            .catch(() => {});
        }
      },
      [feedback, message.id],
    );

    // ─── User message ───
    if (isUser) {
      return (
        <article className="message-row message-row-user">
          <div className="avatar avatar-user" aria-hidden="true">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </div>
          <div className="bubble bubble-user">
            <span className="bubble-role">{t.you}</span>
            <div className="msg-content">{message.content}</div>
            <time className="msg-time">
              {new Date(message.timestamp).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </time>
          </div>
        </article>
      );
    }

    // ─── Assistant message ───
    return (
      <article className="message-row message-row-assistant">
        <div className="avatar avatar-assistant" aria-hidden="true">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 3v18M3 12l3-3 3 3M15 12l3-3 3 3M6 9v9a3 3 0 003 3h6a3 3 0 003-3V9" />
          </svg>
        </div>
        <div className="bubble bubble-assistant">
          {/* Role + badges */}
          <div className="bubble-header">
            <span className="bubble-role">HustleScale</span>
            {message.domain &&
              !["general", "thinking", "clarify", "blocked", "redirect"].includes(
                message.domain,
              ) && (
                <span className="domain-badge">
                  {message.domain.replace(/_/g, " ")}
                </span>
              )}
            {message.confidence && (
              <span
                className={`grounding-pill ${message.confidence === "high" ? "grounding-ok" : message.confidence === "low" ? "grounding-warn" : "grounding-mid"}`}
              >
                {message.confidence === "high"
                  ? t.grounded
                  : message.confidence === "low"
                    ? t.verify
                    : t.medium}
              </span>
            )}
          </div>

          {/* Message body */}
          {!message.content ? null : collapsed ? (
            <p className="md-p" style={{ color: "var(--color-text-muted)" }}>
              {message.content.slice(0, 150)}...
            </p>
          ) : (
            <Markdown content={message.content} />
          )}

          {/* Tool calls used */}
          {message.toolCalls && message.toolCalls.length > 0 && !collapsed && (
            <div className="tools-used" aria-label="Tools used">
              {message.toolCalls.map((tc, i) => (
                <span key={i} className="tool-pill">
                  <svg
                    width="10"
                    height="10"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                  >
                    <path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z" />
                  </svg>
                  {tc.tool.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          )}

          {/* Sources / Citations — expandable */}
          {message.citations &&
            message.citations.length > 0 &&
            !collapsed && (
              <div className="sources-row">
                <details className="citations">
                  <summary>
                    <svg
                      width="12"
                      height="12"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                    >
                      <path d="M12 2L9.19 8.63L2 9.24L7.46 13.97L5.82 21L12 17.27L18.18 21L16.54 13.97L22 9.24L14.81 8.63L12 2Z" />
                    </svg>
                    {t.sources} ({message.citations.length})
                    {message.faithfulness != null && (
                      <span
                        className={`grounding-pill ${message.faithfulness >= 0.6 ? "grounding-ok" : "grounding-warn"}`}
                      >
                        {message.faithfulness >= 0.6 ? t.grounded : t.verify}
                      </span>
                    )}
                  </summary>
                  <ol>
                    {message.citations.map((c, i) => (
                      <li key={i}>
                        <div className="cite-header">
                          <span className="cite-ref">{i + 1}</span>
                          <strong>{c.source}</strong>
                          {c.section && (
                            <span className="cite-meta">{c.section}</span>
                          )}
                        </div>
                        {c.preview && (
                          <div className="cite-passage">
                            {c.preview.slice(0, 200)}
                            {c.preview.length > 200 ? "..." : ""}
                          </div>
                        )}
                      </li>
                    ))}
                  </ol>
                </details>
              </div>
            )}

          {/* Disclaimer */}
          {message.disclaimer && !collapsed && (
            <div className="msg-disclaimer" role="note">
              {message.disclaimer}
            </div>
          )}

          {/* Action bar */}
          {message.content && (
            <div className="bubble-actions">
              <button
                onClick={handleCopy}
                className="action-btn"
                aria-label={copied ? t.copied : t.copy}
              >
                {copied ? (
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="var(--color-green)"
                    strokeWidth="2.5"
                  >
                    <path d="M20 6L9 17l-5-5" />
                  </svg>
                ) : (
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <rect x="9" y="9" width="13" height="13" rx="2" />
                    <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
                  </svg>
                )}
                {copied ? t.copied : t.copy}
              </button>

              {onListen && (
                <button
                  onClick={handleListen}
                  className={`action-btn ${isPlaying ? "action-btn-active-green" : ""}`}
                  aria-label={isPlaying ? t.stop : t.listen}
                >
                  {isPlaying ? (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <rect x="6" y="4" width="4" height="16" rx="1" />
                      <rect x="14" y="4" width="4" height="16" rx="1" />
                    </svg>
                  ) : (
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                    >
                      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                      <path d="M15.54 8.46a5 5 0 010 7.07" />
                    </svg>
                  )}
                  {isPlaying ? t.stop : t.listen}
                </button>
              )}

              {isLong && onToggleCollapse && (
                <button
                  onClick={onToggleCollapse}
                  className="action-btn"
                  aria-expanded={!collapsed}
                >
                  {collapsed ? t.expand : t.collapse}
                </button>
              )}

              <div
                className="feedback-group"
                role="group"
                aria-label="Feedback"
              >
                <button
                  onClick={() => handleFeedback("up")}
                  className={`action-btn ${feedback === "up" ? "action-btn-active-green" : ""}`}
                  aria-label={t.helpful}
                  aria-pressed={feedback === "up"}
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill={feedback === "up" ? "currentColor" : "none"}
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3H14z" />
                    <path d="M7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3" />
                  </svg>
                </button>
                <button
                  onClick={() => handleFeedback("down")}
                  className={`action-btn ${feedback === "down" ? "action-btn-active-red" : ""}`}
                  aria-label={t.notHelpful}
                  aria-pressed={feedback === "down"}
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill={feedback === "down" ? "currentColor" : "none"}
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M10 15v4a3 3 0 003 3l4-9V2H5.72a2 2 0 00-2 1.7l-1.38 9a2 2 0 002 2.3H10z" />
                    <path d="M17 2h2.67A2.31 2.31 0 0122 4v7a2.31 2.31 0 01-2.33 2H17" />
                  </svg>
                </button>
              </div>

              <time className="msg-time">
                {new Date(message.timestamp).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </time>
            </div>
          )}
        </div>
      </article>
    );
  },
  (prev, next) =>
    prev.message.id === next.message.id &&
    prev.message.content === next.message.content &&
    prev.collapsed === next.collapsed &&
    prev.playingId === next.playingId &&
    prev.locale === next.locale,
);
