"use client";

import { stationName, useLangStore, useT } from "@/lib/i18n";
import type { Station } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Churchgate → Virar drawn as a line diagram. Each dot is a station; the
 * number beside it is its open issue count. Clicking a station filters the feed.
 */
export function LineMap({
  stations,
  counts,
  selected,
  onSelect,
}: {
  stations: Station[];
  counts: Record<string, number>;
  selected: string;
  onSelect: (code: string) => void;
}) {
  const ordered = [...stations].sort((a, b) => a.sequence_order - b.sequence_order);
  const t = useT();
  const lang = useLangStore((s) => s.lang);

  return (
    <div className="min-w-0 overflow-hidden border-2 border-foreground/70 bg-card">
      <div className="flex items-center justify-between bg-primary px-4 py-2.5 text-primary-foreground">
        <p className="label-caps text-sm">{t("home.line")}</p>
        {selected && (
          <button
            type="button"
            onClick={() => onSelect("")}
            className="label-caps text-xs text-accent-foreground underline-offset-2 hover:underline"
            style={{ color: "var(--signal)" }}
          >
            {t("home.showAll")}
          </button>
        )}
      </div>

      {/* Phone / tablet: horizontal strip */}
      <div className="overflow-x-auto lg:hidden">
        <ol className="relative flex min-w-max items-start px-4 pb-4 pt-6">
          <span className="absolute left-4 right-4 top-[34px] h-1.5 bg-primary" aria-hidden />
          {ordered.map((st) => {
            const count = counts[st.code] ?? 0;
            const active = selected === st.code;
            return (
              <li key={st.code} className="relative w-[72px] shrink-0">
                <button
                  type="button"
                  onClick={() => onSelect(active ? "" : st.code)}
                  className="group flex w-full flex-col items-center gap-2"
                  aria-pressed={active}
                  aria-label={`${st.name}, ${count} open issues`}
                >
                  <span
                    className={cn(
                      "relative z-10 flex h-5 w-5 items-center justify-center rounded-full border-[3px] border-primary",
                      active ? "bg-accent" : "bg-card group-hover:bg-accent/60"
                    )}
                  />
                  <span className="text-display text-sm leading-tight">{st.code}</span>
                  <span
                    className={cn(
                      "font-board min-w-6 px-1 text-center text-[11px]",
                      count > 0 ? "bg-destructive text-white" : "text-muted-foreground"
                    )}
                  >
                    {count}
                  </span>
                </button>
              </li>
            );
          })}
        </ol>
      </div>

      {/* Desktop: vertical line */}
      <ol className="relative hidden max-h-[620px] overflow-y-auto py-3 pl-5 pr-3 lg:block">
        <span className="absolute bottom-6 left-[27px] top-6 w-1.5 bg-primary" aria-hidden />
        {ordered.map((st) => {
          const count = counts[st.code] ?? 0;
          const active = selected === st.code;
          return (
            <li key={st.code} className="relative">
              <button
                type="button"
                onClick={() => onSelect(active ? "" : st.code)}
                aria-pressed={active}
                className={cn(
                  "group flex w-full items-center gap-3 py-1.5 pr-2 text-left transition-colors",
                  active ? "bg-accent/25" : "hover:bg-muted"
                )}
              >
                <span
                  className={cn(
                    "relative z-10 h-5 w-5 shrink-0 rounded-full border-[3px] border-primary",
                    active ? "bg-accent" : "bg-card group-hover:bg-accent/60"
                  )}
                />
                <span className="min-w-0 flex-1 truncate text-sm font-medium">{stationName(st, lang)}</span>
                <span className="font-board text-[11px] text-muted-foreground">{st.code}</span>
                <span
                  className={cn(
                    "font-board min-w-6 px-1 text-center text-[11px]",
                    count > 0 ? "bg-destructive text-white" : "text-muted-foreground"
                  )}
                >
                  {count}
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
