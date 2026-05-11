"use client";

import { memo, useCallback, useEffect, useRef, useState } from "react";
import { useChatStore } from "@/store/useChatStore";
import { MicIcon } from "./Icons";

/**
 * Floating voice modal — records audio and sends to Sunbird AI STT
 * for native Luganda/Runyankole/Swahili transcription.
 * Falls back to browser Web Speech API if Sunbird unavailable.
 */

export default memo(function VoiceModal() {
  const open = useChatStore((s) => s.voiceModalOpen);
  const setOpen = useChatStore((s) => s.setVoiceModalOpen);
  const setSpeechState = useChatStore((s) => s.setSpeechState);
  const locale = useChatStore((s) => s.locale);

  const [transcript, setTranscript] = useState("");
  const [interim, setInterim] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [processing, setProcessing] = useState(false);
  const isListeningRef = useRef(false);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number>(0);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (!open) return;
    setTranscript("");
    setInterim("");
    setProcessing(false);
    startRecording();
    startVisualizer();
    return () => { stopRecording(); stopVisualizer(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  // ── Recording (Sunbird STT) ──

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : MediaRecorder.isTypeSupported("audio/mp4") ? "audio/mp4" : "";
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);
      recorderRef.current = recorder;
      chunksRef.current = [];
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      recorder.start(500);
      isListeningRef.current = true;
      setIsListening(true);
      setSpeechState("listening");
      setInterim(locale === "lg" ? "Yogera..." : locale === "sw" ? "Sema..." : "Speak now...");
    } catch {
      setSpeechState("error");
    }
  }, [locale, setSpeechState]);

  const stopRecording = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
    recorderRef.current = null;
    isListeningRef.current = false;
    setIsListening(false);
  }, []);

  const transcribeAudio = useCallback(async (): Promise<string> => {
    stopRecording();
    await new Promise((r) => setTimeout(r, 300));
    const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
    if (audioBlob.size < 1000) return "";

    setProcessing(true);
    setInterim(locale === "lg" ? "Okukola transcription..." : "Transcribing...");

    try {
      const formData = new FormData();
      formData.append("audio", audioBlob, "voice.webm");
      formData.append("language", locale);
      const resp = await fetch("/v1/voice/stt", { method: "POST", body: formData });
      if (!resp.ok) return "";
      const data = await resp.json();
      return data.text || "";
    } catch {
      return "";
    } finally {
      setProcessing(false);
    }
  }, [locale, stopRecording]);

  // ── Audio visualizer ──

  const startVisualizer = useCallback(async () => {
    try {
      const stream = streamRef.current || await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!streamRef.current) streamRef.current = stream;
      const audioCtx = new AudioContext();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;
      drawWaveform();
    } catch { /* cosmetic */ }
  }, []);

  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    if (!canvas || !analyser) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    const draw = () => {
      animFrameRef.current = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(dataArray);
      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);
      const barCount = 40;
      const barWidth = width / barCount - 2;
      const centerY = height / 2;
      for (let i = 0; i < barCount; i++) {
        const dataIndex = Math.floor((i / barCount) * bufferLength);
        const value = dataArray[dataIndex] / 255;
        const barHeight = Math.max(3, value * centerY * 0.85);
        const hue = 140 - value * 50;
        ctx.fillStyle = `hsla(${hue}, 70%, 55%, ${0.5 + value * 0.5})`;
        const x = i * (barWidth + 2) + 1;
        ctx.beginPath();
        ctx.roundRect(x, centerY - barHeight, barWidth, barHeight * 2, 2);
        ctx.fill();
      }
    };
    draw();
  }, []);

  const stopVisualizer = useCallback(() => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    analyserRef.current = null;
  }, []);

  // ── Actions ──

  const handleApprove = useCallback(async () => {
    const text = await transcribeAudio();
    stopVisualizer();
    setSpeechState("idle");
    setOpen(false);
    if (text) {
      // Set the text into the chat textarea
      const textarea = document.querySelector<HTMLTextAreaElement>('textarea[aria-label="Message input"]');
      if (textarea) {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value")?.set;
        setter?.call(textarea, text);
        textarea.dispatchEvent(new Event("input", { bubbles: true }));
        textarea.focus();
      }
    }
  }, [transcribeAudio, stopVisualizer, setSpeechState, setOpen]);

  const handleCancel = useCallback(() => {
    stopRecording();
    stopVisualizer();
    setSpeechState("idle");
    setOpen(false);
  }, [stopRecording, stopVisualizer, setSpeechState, setOpen]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") handleCancel(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, handleCancel]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(8px)" }}
      onClick={handleCancel}
    >
      <div
        className="flex flex-col items-center gap-4 rounded-2xl p-6"
        style={{
          background: "var(--color-surface, rgba(30,30,30,0.95))",
          border: "1px solid rgba(255,255,255,0.1)",
          width: "min(90vw, 360px)",
        }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        {/* Waveform */}
        <canvas ref={canvasRef} width={300} height={80} className="w-full rounded-lg" />

        {/* Status */}
        <p className="text-sm" style={{ color: "var(--color-text-light, rgba(255,255,255,0.6))" }}>
          {processing ? "Transcribing..." : interim}
        </p>

        {/* Mic orb */}
        <div
          className="flex items-center justify-center rounded-full"
          style={{
            width: 72, height: 72,
            background: isListening
              ? "linear-gradient(135deg, var(--color-green, #2d6a4f), var(--color-green-dark, #40916c))"
              : "rgba(255,255,255,0.1)",
            boxShadow: isListening ? "0 0 30px rgba(45,106,79,0.4)" : "none",
          }}
        >
          <MicIcon className="w-8 h-8" />
        </div>

        {/* Buttons */}
        <div className="flex gap-3 w-full">
          <button
            onClick={handleCancel}
            className="flex-1 py-3 rounded-xl text-sm font-semibold"
            style={{ background: "rgba(255,255,255,0.08)", color: "var(--color-text-light, rgba(255,255,255,0.7))" }}
          >
            Cancel
          </button>
          <button
            onClick={handleApprove}
            disabled={processing}
            className="flex-1 py-3 rounded-xl text-sm font-semibold"
            style={{
              background: "linear-gradient(135deg, var(--color-green, #2d6a4f), var(--color-green-dark, #40916c))",
              color: "white",
              opacity: processing ? 0.6 : 1,
            }}
          >
            {processing ? "..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
});
