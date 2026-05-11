"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { MicIcon, SendIcon } from "./Icons";
import { useChatStore } from "@/store/useChatStore";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  locale: string;
  prefill?: string;
}

const PLACEHOLDERS: Record<string, string> = {
  en: "Describe your business idea...",
  lg: "Nnyonnyola ekirowoozo kyo eky'omulimu...",
  sw: "Eleza wazo lako la biashara...",
  nyn: "Nyongyera omupango gwawe gw'okukorera...",
};

export function ChatInput({ onSend, disabled, locale, prefill }: ChatInputProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const setVoiceModalOpen = useChatStore((s) => s.setVoiceModalOpen);
  const speechState = useChatStore((s) => s.speechState);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [text]);

  // Auto-focus on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  // Prefill from parent (domain nav)
  useEffect(() => {
    if (prefill) {
      setText(prefill);
      textareaRef.current?.focus();
    }
  }, [prefill]);

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }, [text, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Listen for voice modal transcript via store message
  const message = useChatStore((s) => s.messages);
  useEffect(() => {
    // If store has a pending message from voice modal, it will be in the input
  }, [message]);

  return (
    <div className="flex items-end gap-2">
      {/* Voice input button — opens Sunbird-powered VoiceModal */}
      <button
        onClick={() => setVoiceModalOpen(true)}
        className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl transition-all ${speechState === "listening" ? "animate-pulse" : ""}`}
        style={{
          background: speechState === "listening"
            ? "var(--color-danger, #ef4444)"
            : "var(--color-earth, #8b5e3c)",
          color: "white",
          boxShadow: speechState === "listening"
            ? "0 0 0 4px rgba(239,68,68,0.2)"
            : "0 2px 8px rgba(139,94,60,0.2)",
        }}
        aria-label="Voice input"
        type="button"
        disabled={disabled}
      >
        <MicIcon />
      </button>

      {/* Textarea */}
      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={PLACEHOLDERS[locale] || PLACEHOLDERS.en}
        disabled={disabled}
        rows={1}
        className="input-field flex-1"
        style={{
          minHeight: "48px",
          maxHeight: "160px",
          resize: "none",
          lineHeight: "1.5",
        }}
        aria-label="Message input"
      />

      {/* Send button (upward arrow) */}
      <button
        onClick={handleSend}
        disabled={!text.trim() || disabled}
        className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl transition-all"
        style={{
          background: text.trim()
            ? "linear-gradient(135deg, var(--color-green, #2d6a4f), var(--color-green-dark, #1b4332))"
            : "rgba(0,0,0,0.08)",
          color: text.trim() ? "white" : "var(--color-text-light, #999)",
          boxShadow: text.trim()
            ? "0 4px 12px rgba(45,106,79,0.25)"
            : "none",
          cursor: text.trim() ? "pointer" : "default",
        }}
        aria-label="Send message"
        type="button"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 19V5" />
          <path d="m5 12 7-7 7 7" />
        </svg>
      </button>
    </div>
  );
}
