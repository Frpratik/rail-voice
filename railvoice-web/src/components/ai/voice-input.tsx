"use client";

import { Mic, MicOff } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

// The Web Speech API isn't in TypeScript's DOM types yet; this is the part we use.
interface Recognition {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  start(): void;
  stop(): void;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
}

type RecognitionCtor = new () => Recognition;

function recognitionCtor(): RecognitionCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    SpeechRecognition?: RecognitionCtor;
    webkitSpeechRecognition?: RecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

const LANGS = [
  { code: "hi-IN", label: "हिन्दी" },
  { code: "mr-IN", label: "मराठी" },
  { code: "gu-IN", label: "ગુજરાતી" },
  { code: "en-IN", label: "English" },
];

/** Speak instead of typing. Speech-to-text runs in the browser (on Chrome, via Google's service). */
export function VoiceInput({ onText }: { onText: (text: string) => void }) {
  const [supported, setSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const [lang, setLang] = useState("hi-IN");
  const recognition = useRef<Recognition | null>(null);

  useEffect(() => {
    queueMicrotask(() => setSupported(recognitionCtor() !== null));
    return () => recognition.current?.stop();
  }, []);

  if (!supported) return null;

  const toggle = () => {
    if (listening) {
      recognition.current?.stop();
      return;
    }
    const Ctor = recognitionCtor();
    if (!Ctor) return;
    const rec = new Ctor();
    rec.lang = lang;
    rec.interimResults = false;
    rec.continuous = true;
    rec.onresult = (event) => {
      const parts: string[] = [];
      for (let i = 0; i < event.results.length; i++) parts.push(event.results[i][0].transcript);
      onText(parts.join(" ").trim());
    };
    rec.onerror = (event) => {
      if (event.error === "not-allowed") toast.error("Allow microphone access to speak your report.");
      else if (event.error !== "aborted" && event.error !== "no-speech") toast.error("Couldn't hear that. Please try again.");
    };
    rec.onend = () => setListening(false);
    recognition.current = rec;
    rec.start();
    setListening(true);
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <select
        aria-label="Speaking language"
        value={lang}
        onChange={(e) => setLang(e.target.value)}
        disabled={listening}
        className="h-9 border-2 border-foreground/30 bg-card px-2 text-xs"
      >
        {LANGS.map((l) => (
          <option key={l.code} value={l.code}>
            {l.label}
          </option>
        ))}
      </select>
      <button
        type="button"
        onClick={toggle}
        aria-pressed={listening}
        className={`label-caps inline-flex h-9 items-center gap-1.5 border-2 px-3 text-xs ${
          listening
            ? "border-destructive bg-destructive text-white"
            : "border-foreground/30 text-foreground hover:border-foreground/60"
        }`}
      >
        {listening ? <MicOff className="h-3.5 w-3.5" /> : <Mic className="h-3.5 w-3.5" />}
        {listening ? "Stop" : "Speak instead"}
      </button>
      {listening && <span className="text-xs text-destructive">Listening… speak now</span>}
    </div>
  );
}
