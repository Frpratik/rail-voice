"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Flame, Plus, Search, TrainFront } from "lucide-react";
import { useState } from "react";
import { IssueCard } from "@/components/issues/issue-card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { IssueCardSkeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const SORTS = [
  { value: "most_supported", label: "Most Supported", icon: Flame },
  { value: "newest", label: "Newest", icon: null },
] as const;

export default function HomePage() {
  const [sort, setSort] = useState<"most_supported" | "newest">("most_supported");
  const [selectedStation, setSelectedStation] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const { data: stationsData } = useQuery({
    queryKey: ["stations"],
    queryFn: () => api.stations.list(),
  });

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["issues", sort, selectedStation],
    queryFn: () =>
      api.issues.list({
        sort,
        station_code: selectedStation || undefined,
        limit: 30,
      }),
  });

  const stations = stationsData?.data ?? [];
  const rawIssues = data?.data.items ?? [];

  const filteredIssues = searchQuery.trim()
    ? rawIssues.filter(
        (issue) =>
          (issue.title?.toLowerCase().includes(searchQuery.toLowerCase()) || false) ||
          issue.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
          issue.location.station.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          issue.issue_number.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : rawIssues;

  return (
    <div className="space-y-10">
      {/* Hero Section */}
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
              Western Railway · Churchgate → Virar
            </p>
            <h1 className="text-display text-[2.4rem] font-semibold leading-[1.08] tracking-tight sm:text-5xl lg:text-[3.2rem]">
              Public Voice for Western Railway
            </h1>
            <p className="mt-4 max-w-md text-[15px] leading-relaxed text-muted-foreground sm:text-base">
              Report infrastructure, cleanliness, and safety issues. Upvote critical problems to trigger Station Admin review and escalation to Western Railway authorities.
            </p>
            <div className="mt-7 flex flex-wrap items-center gap-3">
              <Link href="/report">
                <Button variant="accent" size="lg" className="gap-2">
                  <Plus className="h-4 w-4" />
                  Report a Problem
                </Button>
              </Link>
              <Link href="/my-issues">
                <Button variant="outline" size="lg">
                  Track My Reports
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
              { label: "Corridor Stations", value: "28 Stations" },
              { label: "Community Upvotes", value: "1-Click Support" },
              { label: "Station Admin", value: "Official Review" },
              { label: "WR Escalation", value: "Direct Reports" },
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

      {/* Feed Filters & Controls */}
      <section>
        <div className="mb-6 flex flex-col gap-4">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-display text-xl font-semibold tracking-tight">
                Live Problem Feed
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Grievances reported across the Churchgate → Virar corridor
              </p>
            </div>
            <div className="flex gap-1.5 overflow-x-auto pb-1">
              {SORTS.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => setSort(s.value)}
                  className={cn(
                    "inline-flex items-center gap-1.5 shrink-0 rounded-full px-4 py-2 text-xs font-semibold tracking-tight transition-all",
                    sort === s.value
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "bg-card text-muted-foreground ring-1 ring-card-border hover:text-foreground"
                  )}
                >
                  {s.icon && <s.icon className="h-3.5 w-3.5" />}
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by keywords, grievance ID, or station..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 bg-card"
              />
            </div>
            <select
              value={selectedStation}
              onChange={(e) => setSelectedStation(e.target.value)}
              className="h-10 rounded-xl border border-card-border bg-card px-3.5 text-xs font-medium text-foreground transition-colors focus:border-accent focus:outline-none"
            >
              <option value="">All 28 WR Stations</option>
              {stations.map((st) => (
                <option key={st.code} value={st.code}>
                  {st.name} ({st.code})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Feed List */}
        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <IssueCardSkeleton key={i} />
            ))}
          </div>
        ) : error ? (
          <EmptyState
            title="Couldn't load issues"
            description="Unable to connect to the RailVoice API."
            action={{ label: "Retry", onClick: () => refetch() }}
          />
        ) : filteredIssues.length === 0 ? (
          <EmptyState
            title="No grievances found"
            description={
              selectedStation || searchQuery
                ? "No matching problems reported for this filter."
                : "No open grievances on the corridor feed right now."
            }
            action={{
              label: "Report a problem",
              onClick: () => {
                window.location.href = "/report";
              },
            }}
          />
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {filteredIssues.map((issue, i) => (
              <motion.div
                key={issue.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, delay: i * 0.03 }}
              >
                <IssueCard issue={issue} />
              </motion.div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
