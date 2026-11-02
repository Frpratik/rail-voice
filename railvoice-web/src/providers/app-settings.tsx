"use client";

import { useEffect } from "react";
import { useLangStore } from "@/lib/i18n";

const TEXT_SIZE_KEY = "railvoice-text-size";

export type TextSize = "normal" | "large";

export function getTextSize(): TextSize {
  try {
    return localStorage.getItem(TEXT_SIZE_KEY) === "large" ? "large" : "normal";
  } catch {
    return "normal";
  }
}

export function applyTextSize(size: TextSize) {
  document.documentElement.dataset.text = size;
  try {
    localStorage.setItem(TEXT_SIZE_KEY, size);
  } catch {
    /* Private mode: the size still applies for this visit. */
  }
}

/** Restores language and text size, and registers the service worker. */
export function AppSettings() {
  const lang = useLangStore((s) => s.lang);

  useEffect(() => {
    void useLangStore.persist.rehydrate();
    applyTextSize(getTextSize());
    if ("serviceWorker" in navigator && process.env.NODE_ENV === "production") {
      navigator.serviceWorker.register("/sw.js").catch(() => {
        /* The site works without it. */
      });
    }
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  return null;
}
