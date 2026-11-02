"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { EmptyState, PageHeader } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";

export default function LeaderboardPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["leaderboard"],
    queryFn: () => api.public.leaderboard(),
  });
  const board = data?.data;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Community"
        title="Leaderboard"
        description="Points for reports, backing other passengers, useful comments, and problems that got fixed."
      />

      {isLoading ? (
        <Skeleton className="h-40" />
      ) : error || !board ? (
        <EmptyState
          title="Couldn't load the leaderboard"
          description="Check your connection and try again."
          action={{ label: "Try again", onClick: () => refetch() }}
        />
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <section className="min-w-0">
            <h2 className="text-display mb-3 text-2xl">Top passengers</h2>
            <Card className="p-0">
              {board.passengers.length === 0 && (
                <p className="p-5 text-sm text-muted-foreground">No points earned yet.</p>
              )}
              <ol>
                {board.passengers.map((p, i) => (
                  <li
                    key={`${p.display_name}-${i}`}
                    className="flex items-center gap-3 border-b border-card-border px-4 py-3 last:border-0"
                  >
                    <span className="font-board w-6 text-sm text-muted-foreground">{i + 1}</span>
                    <span className="min-w-0 flex-1 truncate font-medium">{p.display_name}</span>
                    <span className="font-board text-sm">{p.points} pts</span>
                  </li>
                ))}
              </ol>
            </Card>
          </section>

          <section className="min-w-0">
            <h2 className="text-display mb-3 text-2xl">Best fix rate</h2>
            <Card className="p-0">
              {board.stations.length === 0 && (
                <p className="p-5 text-sm text-muted-foreground">No station data yet.</p>
              )}
              <ol>
                {board.stations.map((s, i) => (
                  <li key={s.code} className="border-b border-card-border last:border-0">
                    <Link href={`/stations/${s.code}`} className="flex items-center gap-3 px-4 py-3 hover:bg-muted">
                      <span className="font-board w-6 text-sm text-muted-foreground">{i + 1}</span>
                      <span className="min-w-0 flex-1 truncate font-medium">{s.name}</span>
                      <span className="font-board text-sm">{s.fix_rate ?? 0}%</span>
                    </Link>
                  </li>
                ))}
              </ol>
            </Card>
          </section>
        </div>
      )}
    </div>
  );
}
