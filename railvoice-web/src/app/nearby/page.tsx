"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { motion } from "framer-motion";
import { IssueCard } from "@/components/issues/issue-card";
import { PageHeader, EmptyState } from "@/components/ui/empty-state";
import { IssueCardSkeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { Inbox } from "lucide-react";
import { cn } from "@/lib/utils";

export default function NearbyPage() {
  const { data: stationsData } = useQuery({
    queryKey: ["stations"],
    queryFn: () => api.stations.list({ zone_code: "WR" }),
  });

  const { data: issuesData, isLoading } = useQuery({
    queryKey: ["issues", "nearby"],
    queryFn: () => api.issues.list({ sort: "newest", limit: 12 }),
  });

  const stations = stationsData?.data ?? [];
  const issues = issuesData?.data.items ?? [];

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Corridor"
        title="Churchgate → Virar"
        description="Browse every station on the Western Railway suburban line."
      />

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="relative -mx-4 flex gap-2 overflow-x-auto px-4 pb-2 sm:mx-0 sm:px-0"
      >
        {stations.map((s, i) => (
          <Link
            key={s.id}
            href={`/stations/${s.code}`}
            className={cn(
              "shrink-0 rounded-2xl border border-card-border bg-card px-4 py-3 transition-all hover:-translate-y-0.5 hover:border-accent/30 hover:shadow-md",
              i === 0 && "border-accent/40"
            )}
          >
            <p className="font-mono text-[11px] font-semibold text-accent">{s.code}</p>
            <p className="mt-0.5 text-sm font-medium tracking-tight">{s.name}</p>
          </Link>
        ))}
      </motion.div>

      <div>
        <h2 className="mb-4 text-display text-lg font-semibold tracking-tight">
          Recent across the line
        </h2>
        <div className="grid gap-4">
          {isLoading &&
            Array.from({ length: 3 }).map((_, i) => <IssueCardSkeleton key={i} />)}
          {!isLoading && issues.length === 0 && (
            <EmptyState
              icon={Inbox}
              title="Quiet corridor"
              description="No recent issues. Check back soon or report something you notice."
              actionLabel="Report an issue"
              actionHref="/report"
            />
          )}
          {issues.map((issue, i) => (
            <IssueCard key={issue.id} issue={issue} index={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
