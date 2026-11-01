"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, MapPin, Search, TrainFront } from "lucide-react";
import { Card } from "@/components/ui/card";
import { EmptyState, PageHeader } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";

export default function StationsDirectoryPage() {
  const [search, setSearch] = useState("");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["stations"],
    queryFn: () => api.stations.list({ zone_code: "WR" }),
  });

  const stations = data?.data ?? [];

  const filtered = search.trim()
    ? stations.filter(
        (s) =>
          s.name.toLowerCase().includes(search.toLowerCase()) ||
          s.code.toLowerCase().includes(search.toLowerCase()) ||
          (s.name_hi && s.name_hi.includes(search)) ||
          (s.name_mr && s.name_mr.includes(search))
      )
    : stations;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Corridor Directory"
        title="Western Railway Stations"
        description="Browse all suburban stations between Churchgate and Virar. Check station-specific grievances and reports."
      />

      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search station by name or code (e.g. Bandra, BA, Andheri, CCG)..."
          className="pl-10"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 9 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-2xl" />
          ))}
        </div>
      )}

      {error && (
        <EmptyState
          title="Could not load stations"
          description="Failed to connect to the backend corridor API."
          action={{ label: "Retry", onClick: () => void refetch() }}
        />
      )}

      {!isLoading && !error && filtered.length === 0 && (
        <EmptyState
          title="No stations found"
          description={`No Western Railway station matching "${search}".`}
        />
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((st, index) => (
          <motion.div
            key={st.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: Math.min(index * 0.03, 0.3), duration: 0.3 }}
          >
            <Link href={`/stations/${st.code}`} className="block group">
              <Card className="p-0 transition-colors group-hover:border-foreground/60">
                <div className="flex items-start justify-between p-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-primary text-primary-foreground group-hover:bg-accent group-hover:text-accent-foreground transition-colors">
                      <TrainFront className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="text-display text-xl text-foreground group-hover:text-accent transition-colors">
                        {st.name}
                      </h3>
                      <p className="font-board text-xs text-muted-foreground">
                        {st.code} · Seq #{st.sequence_order}
                      </p>
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-foreground" />
                </div>

                <div className="flex items-center justify-between border-t-2 border-dashed border-card-border bg-muted/50 px-4 py-2.5 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" />
                    {st.division?.name ?? "Mumbai Division"}
                  </span>
                  <span className="font-board bg-primary px-2 py-0.5 text-primary-foreground">
                    {st.open_issue_count ?? 0} open
                  </span>
                </div>
              </Card>
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
