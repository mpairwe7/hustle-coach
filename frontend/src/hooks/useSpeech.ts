"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  startASR,
  stopASR,
  hasASRSupport,
  hasTTSSupport,
  speak,
  stopSpeaking,
} from "@/services/voiceService";

// ─── ASR Hook — voice input ───

interface UseASROptions {
  locale: string;
  onTranscript: (text: string) => void;
}

export function useASR({ locale, onTranscript }: UseASROptions) {
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const supported = useRef(false);

  useEffect(() => {
    supported.current = hasASRSupport();
  }, []);

  const toggle = useCallback(() => {
    setError(null);

    if (isListening) {
      stopASR();
      setIsListening(false);
      return;
    }

    if (!supported.current) {
      setError("Speech recognition is not supported in this browser.");
      return;
    }

    const started = startASR(locale, {
      onResult: ({ transcript }) => {
        onTranscript(transcript);
      },
      onEnd: () => {
        setIsListening(false);
      },
      onError: (msg) => {
        setError(msg);
        setIsListening(false);
      },
    });

    if (started) {
      setIsListening(true);
    }
  }, [isListening, locale, onTranscript]);

  // Cleanup on unmount
  useEffect(() => {
    return () => stopASR();
  }, []);

  return {
    isListening,
    error,
    toggle,
    supported: supported.current,
    clearError: () => setError(null),
  };
}

// ─── TTS Hook — listen to messages ───

export function useTTS(locale: string) {
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const supported = useRef(false);

  useEffect(() => {
    supported.current = hasTTSSupport();
    // Pre-load voices (some browsers need this)
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.getVoices();
      // Chrome fires voiceschanged event
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }
  }, []);

  const play = useCallback(
    (turnId: string, text: string) => {
      setError(null);

      // If already playing this message, stop it
      if (playingId === turnId) {
        stopSpeaking();
        setPlayingId(null);
        return;
      }

      if (!supported.current) {
        setError("Text-to-speech is not supported in this browser.");
        return;
      }

      speak(text, locale, {
        onStart: () => setPlayingId(turnId),
        onEnd: () => setPlayingId(null),
        onError: (msg) => {
          setError(msg);
          setPlayingId(null);
        },
      });
    },
    [playingId, locale],
  );

  const stop = useCallback(() => {
    stopSpeaking();
    setPlayingId(null);
  }, []);

  // Stop on unmount
  useEffect(() => {
    return () => stopSpeaking();
  }, []);

  return {
    playingId,
    error,
    play,
    stop,
    supported: supported.current,
    clearError: () => setError(null),
  };
}
