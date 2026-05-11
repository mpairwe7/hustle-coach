/**
 * HustleScale Voice Service — browser-native speech recognition & TTS.
 *
 * Uses Web Speech API for both input (ASR) and output (TTS).
 * No server-side speech endpoints required — works offline on supported browsers.
 */

// ─── Browser support detection ───

export function hasASRSupport(): boolean {
  return !!(
    typeof window !== "undefined" &&
    (window.SpeechRecognition || window.webkitSpeechRecognition)
  );
}

export function hasTTSSupport(): boolean {
  return !!(typeof window !== "undefined" && window.speechSynthesis);
}

// ─── Language mapping for Uganda ───

const ASR_LANG_MAP: Record<string, string> = {
  en: "en-UG",
  lg: "lg-UG",
  sw: "sw-KE",
  nyn: "nyn-UG",
};

const TTS_LANG_MAP: Record<string, string> = {
  en: "en-US",
  lg: "en-US", // Luganda TTS not widely available — fallback to English
  sw: "sw-KE",
  nyn: "en-US", // Runyankole fallback
};

// ─── Speech Recognition (ASR) ───

export interface ASRResult {
  transcript: string;
  isFinal: boolean;
  confidence: number;
}

export interface ASRCallbacks {
  onResult: (result: ASRResult) => void;
  onEnd: () => void;
  onError: (error: string) => void;
}

let activeRecognition: SpeechRecognition | null = null;

export function startASR(locale: string, callbacks: ASRCallbacks): boolean {
  // Stop any existing recognition
  stopASR();

  const SR = typeof window !== "undefined"
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : undefined;

  if (!SR) {
    callbacks.onError("Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.");
    return false;
  }

  try {
    const recognition = new SR();
    recognition.lang = ASR_LANG_MAP[locale] || "en-UG";
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let transcript = "";
      let isFinal = false;
      let confidence = 0;

      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        transcript += result[0].transcript;
        if (result.isFinal) {
          isFinal = true;
          confidence = result[0].confidence;
        }
      }

      callbacks.onResult({ transcript, isFinal, confidence });
    };

    recognition.onend = () => {
      activeRecognition = null;
      callbacks.onEnd();
    };

    recognition.onerror = (event: Event) => {
      activeRecognition = null;
      const errorEvent = event as Event & { error?: string };
      const errorCode = errorEvent.error || "unknown";

      // Map browser error codes to user-friendly messages
      const messages: Record<string, string> = {
        "not-allowed": "Microphone access denied. Please allow microphone access in your browser settings.",
        "no-speech": "No speech detected. Please try again and speak clearly.",
        "network": "Network error. Speech recognition requires an internet connection on this browser.",
        "audio-capture": "No microphone found. Please connect a microphone and try again.",
        "aborted": "", // User cancelled — silent
      };

      const message = messages[errorCode] || `Voice input error: ${errorCode}`;
      if (message) {
        callbacks.onError(message);
      }
      callbacks.onEnd();
    };

    recognition.start();
    activeRecognition = recognition;
    return true;
  } catch (err) {
    callbacks.onError("Could not start voice input. Please try again.");
    return false;
  }
}

export function stopASR(): void {
  if (activeRecognition) {
    try {
      activeRecognition.stop();
    } catch {
      // Already stopped
    }
    activeRecognition = null;
  }
}

export function isASRActive(): boolean {
  return activeRecognition !== null;
}

// ─── Text-to-Speech (TTS) ───

let currentUtterance: SpeechSynthesisUtterance | null = null;

export function speak(
  text: string,
  locale: string,
  callbacks?: {
    onStart?: () => void;
    onEnd?: () => void;
    onError?: (error: string) => void;
  },
): boolean {
  if (!hasTTSSupport()) {
    callbacks?.onError?.("Text-to-speech is not supported in this browser.");
    return false;
  }

  // Stop any current speech
  stopSpeaking();

  // Clean markdown/formatting from text before speaking
  const cleanText = text
    .replace(/```[\s\S]*?```/g, "") // Remove code blocks
    .replace(/\*\*(.+?)\*\*/g, "$1") // Remove bold markers
    .replace(/\*(.+?)\*/g, "$1") // Remove italic markers
    .replace(/`([^`]+)`/g, "$1") // Remove inline code
    .replace(/#{1,4}\s+/g, "") // Remove heading markers
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1") // Links → text only
    .replace(/[|]/g, ", ") // Table pipes → commas
    .replace(/[-*]\s+/g, "") // Remove list markers
    .replace(/\d+[.)]\s+/g, "") // Remove numbered list markers
    .replace(/\n{2,}/g, ". ") // Double newlines → pause
    .replace(/\n/g, " ") // Single newlines → space
    .replace(/\s{2,}/g, " ") // Collapse whitespace
    .trim();

  if (!cleanText) {
    callbacks?.onEnd?.();
    return false;
  }

  try {
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = TTS_LANG_MAP[locale] || "en-US";
    utterance.rate = 0.92;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Try to find a good voice for the language
    const voices = window.speechSynthesis.getVoices();
    const targetLang = TTS_LANG_MAP[locale] || "en";
    const preferredVoice = voices.find(
      (v) => v.lang.startsWith(targetLang.split("-")[0]) && !v.localService,
    ) || voices.find(
      (v) => v.lang.startsWith(targetLang.split("-")[0]),
    );
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    utterance.onstart = () => callbacks?.onStart?.();
    utterance.onend = () => {
      currentUtterance = null;
      callbacks?.onEnd?.();
    };
    utterance.onerror = (event) => {
      currentUtterance = null;
      if (event.error !== "interrupted" && event.error !== "canceled") {
        callbacks?.onError?.("Could not play audio. Please try again.");
      }
      callbacks?.onEnd?.();
    };

    currentUtterance = utterance;
    window.speechSynthesis.speak(utterance);
    return true;
  } catch {
    callbacks?.onError?.("Could not start text-to-speech. Please try again.");
    return false;
  }
}

export function stopSpeaking(): void {
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  currentUtterance = null;
}

export function isSpeaking(): boolean {
  return !!(typeof window !== "undefined" && window.speechSynthesis?.speaking);
}
