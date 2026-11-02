"use client";

import { useQuery } from "@tanstack/react-query";
import { Languages } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";

const LANGS = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "mr", label: "मराठी" },
  { code: "gu", label: "ગુજરાતી" },
];

/** Read a report in another language. Translations are written by AI and cached on the server. */
export function TranslateReport({ issueId }: { issueId: string }) {
  const [lang, setLang] = useState<string | null>(null);
  const { data: aiStatus } = useQuery({ queryKey: ["ai-status"], queryFn: () => api.ai.status() });
  const { data, isFetching, error } = useQuery({
    queryKey: ["translate", issueId, lang],
    queryFn: () => api.ai.translate(issueId, lang!),
    enabled: !!lang,
    retry: false,
    staleTime: Infinity,
  });

  if (!aiStatus?.data.enabled) return null;

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-1.5">
        <Languages className="h-4 w-4 text-muted-foreground" />
        <span className="text-xs text-muted-foreground">Read in:</span>
        {LANGS.map((l) => (
          <button
            key={l.code}
            type="button"
            onClick={() => setLang(lang === l.code ? null : l.code)}
            aria-pressed={lang === l.code}
            className={`border px-2 py-0.5 text-xs ${
              lang === l.code ? "border-primary bg-primary text-primary-foreground" : "border-foreground/30"
            }`}
          >
            {l.label}
          </button>
        ))}
      </div>
      {lang && (
        <div className="border-l-4 border-accent bg-muted/50 px-3 py-2 text-sm">
          {isFetching ? (
            <p className="text-muted-foreground">Translating…</p>
          ) : error || !data ? (
            <p className="text-muted-foreground">Translation isn&apos;t available right now.</p>
          ) : (
            <>
              {data.data.title && <p className="font-semibold">{data.data.title}</p>}
              <p className="whitespace-pre-wrap leading-relaxed">{data.data.description}</p>
              <p className="mt-1 text-[11px] text-muted-foreground">Translated by AI. The original is above.</p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
