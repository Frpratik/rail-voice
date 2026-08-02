"use client";

import * as React from "react";
import { Award, ShieldCheck, Trophy, Flame, CheckCircle2 } from "lucide-react";

interface StationLeaderboardEntry {
  rank: number;
  station_id: string;
  station_code: string;
  station_name: string;
  total_issues: number;
  resolved_issues: number;
  resolution_rate_pct: number;
}

interface UserLeaderboardEntry {
  rank: number;
  user_id: string;
  display_name: string;
  avatar_url: string | null;
  points: number;
  tier: string;
  badge_slugs: string[];
  reports_count: number;
}

export default function LeaderboardPage() {
  const [tab, setTab] = React.useState<"stations" | "champions">("stations");
  const [stations, setStations] = React.useState<StationLeaderboardEntry[]>([]);
  const [users, setUsers] = React.useState<UserLeaderboardEntry[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [stRes, uRes] = await Promise.all([
          fetch("/api/v1/gamification/leaderboard/stations"),
          fetch("/api/v1/gamification/leaderboard/users"),
        ]);
        if (stRes.ok) {
          const stJson = await stRes.json();
          setStations(stJson.data || []);
        }
        if (uRes.ok) {
          const uJson = await uRes.json();
          setUsers(uJson.data || []);
        }
      } catch {
        // Handle error silently
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-8">
      {/* Header */}
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2 text-accent">
            <Trophy className="h-6 w-6" />
            <span className="text-xs font-bold uppercase tracking-widest">
              Community Leaderboard
            </span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">
            Corridor Rankings & Civic Champions
          </h1>
          <p className="text-sm text-muted-foreground">
            Gamified performance tracking across Western Railway stations and passenger contributors.
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="flex rounded-xl bg-muted p-1 border border-border">
          <button
            onClick={() => setTab("stations")}
            className={`rounded-lg px-4 py-2 text-xs font-bold transition-all ${
              tab === "stations"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Station Rankings
          </button>
          <button
            onClick={() => setTab("champions")}
            className={`rounded-lg px-4 py-2 text-xs font-bold transition-all ${
              tab === "champions"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Civic Champions
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center rounded-2xl border border-border bg-card">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        </div>
      ) : tab === "stations" ? (
        <div className="grid gap-4">
          {stations.map((st) => (
            <div
              key={st.station_id}
              className="flex items-center justify-between rounded-2xl border border-border/80 bg-card p-5 shadow-sm transition-all hover:border-accent/40"
            >
              <div className="flex items-center gap-4">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-xl font-extrabold text-sm ${
                    st.rank === 1
                      ? "bg-amber-500/20 text-amber-500"
                      : st.rank === 2
                      ? "bg-slate-400/20 text-slate-400"
                      : st.rank === 3
                      ? "bg-amber-700/20 text-amber-700"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  #{st.rank}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-base">{st.station_name}</span>
                    <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono uppercase text-muted-foreground">
                      {st.station_code}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {st.resolved_issues} resolved of {st.total_issues} reported grievances
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div className="flex items-center justify-end gap-1.5 text-emerald-500 font-extrabold text-lg">
                  <CheckCircle2 className="h-5 w-5" />
                  {st.resolution_rate_pct}%
                </div>
                <div className="text-[10px] text-muted-foreground uppercase font-semibold tracking-wider">
                  Resolution Rate
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid gap-4">
          {users.map((u) => (
            <div
              key={u.user_id}
              className="flex items-center justify-between rounded-2xl border border-border/80 bg-card p-5 shadow-sm transition-all hover:border-accent/40"
            >
              <div className="flex items-center gap-4">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-xl font-extrabold text-sm ${
                    u.rank === 1
                      ? "bg-amber-500/20 text-amber-500"
                      : u.rank === 2
                      ? "bg-slate-400/20 text-slate-400"
                      : u.rank === 3
                      ? "bg-amber-700/20 text-amber-700"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  #{u.rank}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-base">{u.display_name}</span>
                    <span className="rounded-full bg-accent/10 px-2 py-0.5 text-[10px] font-bold uppercase text-accent">
                      {u.tier} Tier
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {u.reports_count} verified issue reports submitted
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div className="flex items-center justify-end gap-1 text-amber-500 font-extrabold text-lg">
                  <Flame className="h-5 w-5" />
                  {u.points} pts
                </div>
                <div className="text-[10px] text-muted-foreground uppercase font-semibold tracking-wider">
                  Karma Score
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
