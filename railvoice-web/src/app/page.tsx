"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Search, Sparkles, TrainFront } from "lucide-react";
import { useState } from "react";
import { IssueCard } from "@/components/issues/issue-card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { IssueCardSkeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const SORTS = [
  { value: "newest", label: "Newest" },
  { value: "most_supported", label: "Most supported" },
  { value: "ai_priority", label: "AI priority" },
  { value: "trending", label: "Trending" },
];

export default function HomePage() {
  const [sort, setSort] = useState("newest");
  const [searchInput, setSearchInput] = useState("");
  const [searchQ, setSearchQ] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["issues", sort],
    queryFn: () => api.issues.list({ sort, limit: 20 }),
    enabled: searchQ.length < 2,
  });

  const {
    data: searchData,
    isLoading: searchLoading,
    error: searchError,
  } = useQuery({
    queryKey: ["search", searchQ],
    queryFn: () => api.search.text(searchQ, { limit: 20 }),
    enabled: searchQ.length >= 2,
  });

  const issues =
    searchQ.length >= 2
      ? (searchData?.data.results ?? []).map((r) => r.issue)
      : (data?.data.items ?? []);
  const feedLoading = searchQ.length >= 2 ? searchLoading : isLoading;
  const feedError = searchQ.length >= 2 ? searchError : error;

  return (
    <div className="space-y-10">
      <section className="relative overflow-hidden rounded-[28px] border border-card-border bg-card noise-overlay">
        <div className="pointer-events-none absolute -right-20 -top-24 h-72 w-72 rounded-full bg-accent/15 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-24 left-10 h-64 w-64 rounded-full bg-success/10 blur-3xl" />

        <div className="relative grid gap-8 p-7 sm:p-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-end lg:p-12">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-card-border bg-background/60 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground backdrop-blur">
              <TrainFront className="h-3.5 w-3.5 text-accent" />
              Western Railway · CCG → VR
            </p>
            <h1 className="text-display text-[2.55rem] font-semibold leading-[1.05] tracking-tight sm:text-5xl lg:text-[3.4rem]">
              RailVoice
            </h1>
            <p className="mt-4 max-w-md text-[15px] leading-relaxed text-muted-foreground sm:text-base">
              Report station and train issues in seconds. AI finds duplicates so
              your support strengthens existing reports — not noise.
            </p>
            <div className="mt-7 flex flex-wrap items-center gap-3">
              <Link href="/report">
                <Button variant="accent" size="lg">
                  Report an issue
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/nearby">
                <Button variant="outline" size="lg">
                  Explore corridor
                </Button>
              </Link>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15, duration: 0.5 }}
            className="grid grid-cols-2 gap-3"
          >
            {[
              { label: "Stations live", value: "29" },
              { label: "AI matches", value: "Semantic" },
              { label: "Support model", value: "Community" },
              { label: "Tracking", value: "Full timeline" },
            ].map((stat) => (
              <div
                key={stat.label}
                className="rounded-2xl border border-card-border bg-background/50 p-4 backdrop-blur"
              >
                <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
                  {stat.label}
                </p>
                <p className="mt-2 text-display text-lg font-semibold tracking-tight">
                  {stat.value}
                </p>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      <section>
        <div className="mb-5 flex flex-col gap-4">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-display text-xl font-semibold tracking-tight">
                Live issues
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Ranked across the Churchgate → Virar corridor
              </p>
            </div>
            <div className="flex gap-1.5 overflow-x-auto pb-1">
              {SORTS.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => {
                    setSort(s.value);
                    setSearchQ("");
                    setSearchInput("");
                  }}
                  className={cn(
                    "shrink-0 rounded-full px-3.5 py-2 text-xs font-semibold tracking-tight transition-all",
                    sort === s.value && searchQ.length < 2
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "bg-card text-muted-foreground ring-1 ring-card-border hover:text-foreground"
                  )}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              setSearchQ(searchInput.trim());
            }}
          >
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search issues — litter, lift, platform…"
                className="pl-10"
                aria-label="Search issues"
              />
            </div>
            <Button type="submit" variant="outline" disabled={searchInput.trim().length < 2}>
              Search
            </Button>
            {searchQ.length >= 2 && (
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setSearchQ("");
                  setSearchInput("");
                }}
              >
                Clear
              </Button>
            )}
          </form>
        </div>

        {feedError && (
          <div className="mb-5 rounded-2xl border border-destructive/25 bg-destructive/5 px-5 py-4 text-sm text-destructive">
            Couldn’t load issues. Is the API running at{" "}
            <span className="font-mono text-xs">
              {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
            </span>
            ?
          </div>
        )}

        <div className="grid gap-4">
          {feedLoading &&
            Array.from({ length: 4 }).map((_, i) => <IssueCardSkeleton key={i} />)}

          {!feedLoading && issues.length === 0 && (
            <EmptyState
              icon={Sparkles}
              title={searchQ.length >= 2 ? "No matches" : "No issues yet"}
              description={
                searchQ.length >= 2
                  ? "Try a different phrase or clear search to browse the live feed."
                  : "Be the first to report something on the corridor. Your voice helps stations act faster."
              }
              actionLabel="Report an issue"
              actionHref="/report"
            />
          )}

          {issues.map((issue, i) => (
            <IssueCard key={issue.id} issue={issue} index={i} />
          ))}
        </div>
      </section>
    </div>
  );
}
