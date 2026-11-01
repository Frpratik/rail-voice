"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Plus, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { LineMap } from "@/components/home/line-map";
import { IssueCard } from "@/components/issues/issue-card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { IssueCardSkeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const CLOSED = new Set(["closed", "rejected", "spam", "duplicate_merged", "withdrawn"]);

const SORTS = [
  { value: "most_supported", label: "Most supported" },
  { value: "newest", label: "Newest" },
] as const;

export default function HomePage() {
  const [sort, setSort] = useState<"most_supported" | "newest">("most_supported");
  const [selectedStation, setSelectedStation] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const { data: stationsData } = useQuery({
    queryKey: ["stations"],
    queryFn: () => api.stations.list(),
  });

  // Everything, for the line-map counts and the headline numbers.
  const { data: allData } = useQuery({
    queryKey: ["issues-all"],
    queryFn: () => api.issues.list({ sort: "newest", limit: 100 }),
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

  const stations = useMemo(() => stationsData?.data ?? [], [stationsData]);
  const rawIssues = data?.data.items ?? [];
  const allIssues = useMemo(() => allData?.data.items ?? [], [allData]);

  const counts = useMemo(() => {
    const out: Record<string, number> = {};
    for (const issue of allIssues) {
      if (CLOSED.has(issue.status)) continue;
      const code = issue.location.station.code;
      out[code] = (out[code] ?? 0) + 1;
    }
    return out;
  }, [allIssues]);

  const openCount = Object.values(counts).reduce((a, b) => a + b, 0);
  const urgentCount = allIssues.filter((i) => i.is_emergency && !CLOSED.has(i.status)).length;
  const resolvedCount = allIssues.filter((i) =>
    ["completed", "verified_complete", "closed"].includes(i.status)
  ).length;

  const q = searchQuery.trim().toLowerCase();
  const filteredIssues = q
    ? rawIssues.filter(
        (issue) =>
          issue.title?.toLowerCase().includes(q) ||
          issue.description.toLowerCase().includes(q) ||
          issue.location.station.name.toLowerCase().includes(q) ||
          issue.issue_number.toLowerCase().includes(q)
      )
    : rawIssues;

  const selectedName = stations.find((s) => s.code === selectedStation)?.name;

  return (
    <div className="space-y-8">
      {/* Name board */}
      <section className="name-board">
        <div className="grid gap-6 p-6 sm:p-8 lg:grid-cols-[1fr_auto] lg:items-center">
          <div>
            <p className="label-caps text-sm text-[#10275c]">Western Railway · Suburban</p>
            <h1 className="text-display mt-1 text-5xl uppercase leading-none sm:text-6xl">
              Churchgate <span className="text-[#c8102e]">→</span> Virar
            </h1>
            <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-[#101a33]/75">
              Broken lift, dirty platform, unsafe edge? Report it here. Other passengers back the
              report, and the station office sees the most-supported problems first.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link href="/report">
                <Button variant="accent" size="lg" className="gap-2">
                  <Plus className="h-4 w-4" />
                  Report a problem
                </Button>
              </Link>
              <Link href="/my-issues">
                <Button
                  variant="outline"
                  size="lg"
                  className="border-[#101a33] text-[#101a33] hover:bg-[#101a33] hover:text-white"
                >
                  My reports
                </Button>
              </Link>
            </div>
          </div>

          <dl className="grid grid-cols-3 gap-px bg-[#101a33]/25 text-center lg:min-w-[320px]">
            {[
              { label: "Open", value: openCount },
              { label: "Urgent", value: urgentCount },
              { label: "Fixed", value: resolvedCount },
            ].map((stat) => (
              <div key={stat.label} className="bg-white px-4 py-3">
                <dd className="font-board text-3xl font-medium text-[#101a33]">{stat.value}</dd>
                <dt className="label-caps text-xs text-[#101a33]/70">{stat.label}</dt>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <div className="sleepers" aria-hidden />

      <div className="grid gap-8 lg:grid-cols-[300px_1fr] lg:items-start">
        <aside className="lg:sticky lg:top-24">
          <LineMap
            stations={stations}
            counts={counts}
            selected={selectedStation}
            onSelect={setSelectedStation}
          />
        </aside>

        <section className="min-w-0">
          <div className="mb-5 flex flex-col gap-4">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 className="text-display text-3xl">
                  {selectedName ? `${selectedName} station` : "All stations"}
                </h2>
                <p className="mt-0.5 text-sm text-muted-foreground">
                  {filteredIssues.length} {filteredIssues.length === 1 ? "report" : "reports"}
                </p>
              </div>
              <div className="flex gap-1">
                {SORTS.map((s) => (
                  <button
                    key={s.value}
                    type="button"
                    onClick={() => setSort(s.value)}
                    className={cn(
                      "label-caps border-2 px-3 py-1.5 text-xs transition-colors",
                      sort === s.value
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-foreground/30 text-muted-foreground hover:border-foreground/60 hover:text-foreground"
                    )}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="relative">
              <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by keyword, report number or station"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {isLoading ? (
            <div className="grid gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <IssueCardSkeleton key={i} />
              ))}
            </div>
          ) : error ? (
            <EmptyState
              title="Couldn't load reports"
              description="The RailVoice server isn't responding. Check your connection and try again."
              action={{ label: "Try again", onClick: () => refetch() }}
            />
          ) : filteredIssues.length === 0 ? (
            <EmptyState
              title="No reports here"
              description={
                selectedStation || searchQuery
                  ? "Nothing matches this filter."
                  : "No problems have been reported yet."
              }
              action={{ label: "Report a problem", href: "/report" }}
            />
          ) : (
            <div className="grid gap-4">
              {filteredIssues.map((issue) => (
                <IssueCard key={issue.id} issue={issue} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
