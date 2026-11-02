"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { LocateFixed, Plus, Search, Star } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { LineMap } from "@/components/home/line-map";
import { IssueCard } from "@/components/issues/issue-card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { IssueCardSkeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { useT } from "@/lib/i18n";
import { currentPosition } from "@/lib/image";
import { cn } from "@/lib/utils";

const CLOSED = new Set(["closed", "rejected", "spam", "duplicate_merged", "withdrawn"]);

const SORTS = [
  { value: "most_supported", label: "sort.most_supported" },
  { value: "urgent", label: "sort.urgent" },
  { value: "newest", label: "sort.newest" },
] as const;

export default function HomePage() {
  const t = useT();
  const user = useAuthStore((s) => s.user);
  const [sort, setSort] = useState<"most_supported" | "newest" | "urgent">("most_supported");
  const [selectedStation, setSelectedStation] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [category, setCategory] = useState("");
  const [openOnly, setOpenOnly] = useState(false);
  const [myStationsOnly, setMyStationsOnly] = useState(false);
  const [locating, setLocating] = useState(false);

  const { data: categoriesData } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.categories.list(),
  });

  const { data: favouritesData } = useQuery({
    queryKey: ["favourites"],
    queryFn: () => api.me.favourites(),
    enabled: !!user,
  });
  const favourites = useMemo(() => favouritesData?.data.codes ?? [], [favouritesData]);

  const nearMe = async () => {
    setLocating(true);
    const position = await currentPosition();
    if (!position) {
      setLocating(false);
      toast.error("Couldn't get your location. Check your browser's location permission.");
      return;
    }
    try {
      const res = await api.stations.nearest(position.coords.latitude, position.coords.longitude);
      const nearest = res.data.items[0];
      if (nearest) {
        setSelectedStation(nearest.code);
        toast.success(`Nearest station: ${nearest.name} (${nearest.distance_km} km)`);
      }
    } catch {
      toast.error("Couldn't find the nearest station.");
    } finally {
      setLocating(false);
    }
  };

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
    queryKey: ["issues", sort, selectedStation, category, openOnly, myStationsOnly],
    queryFn: () =>
      api.issues.list({
        sort,
        station_code: selectedStation || undefined,
        category_code: category || undefined,
        open_only: openOnly,
        limit: myStationsOnly ? 100 : 30,
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
  const stationIssues = myStationsOnly
    ? rawIssues.filter((issue) => favourites.includes(issue.location.station.code))
    : rawIssues;
  const filteredIssues = q
    ? stationIssues.filter(
        (issue) =>
          issue.title?.toLowerCase().includes(q) ||
          issue.description.toLowerCase().includes(q) ||
          issue.location.station.name.toLowerCase().includes(q) ||
          issue.issue_number.toLowerCase().includes(q)
      )
    : stationIssues;

  const selectedName = stations.find((s) => s.code === selectedStation)?.name;

  return (
    <div className="space-y-8">
      {/* Name board */}
      <section className="name-board">
        <div className="grid grid-cols-1 gap-6 p-5 sm:p-8 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
          <div>
            <p className="label-caps text-sm text-[#10275c]">Western Railway · Suburban</p>
            <h1 className="text-display mt-1 whitespace-nowrap text-[clamp(1.5rem,8.6vw,3.75rem)] uppercase leading-none">
              Churchgate <span className="text-[#c8102e]">→</span> Virar
            </h1>
            <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-[#101a33]/75">
              {t("home.tagline")}
            </p>
            <div className="mt-5 grid grid-cols-1 gap-3 sm:flex sm:flex-wrap">
              <Link href="/report">
                <Button variant="accent" size="lg" className="w-full gap-2 sm:w-auto">
                  <Plus className="h-4 w-4" />
                  {t("home.report")}
                </Button>
              </Link>
              <Link href="/my-issues">
                <Button
                  variant="outline"
                  size="lg"
                  className="w-full border-[#101a33] text-[#101a33] hover:bg-[#101a33] hover:text-white sm:w-auto"
                >
                  {t("home.myReports")}
                </Button>
              </Link>
            </div>
          </div>

          <dl className="grid grid-cols-3 gap-px bg-[#101a33]/25 text-center lg:min-w-[320px]">
            {[
              { label: t("home.open"), value: openCount },
              { label: t("home.urgent"), value: urgentCount },
              { label: t("home.fixed"), value: resolvedCount },
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

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[300px_minmax(0,1fr)] lg:items-start lg:gap-8">
        <aside className="min-w-0 lg:sticky lg:top-24">
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
                <h2 className="text-display text-2xl sm:text-3xl">
                  {selectedName ?? t("home.allStations")}
                </h2>
                <p className="mt-0.5 text-sm text-muted-foreground">
                  {filteredIssues.length} {t("home.reports")}
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
                    {t(s.label)}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => void nearMe()}
                disabled={locating}
                className="label-caps inline-flex items-center gap-1.5 border-2 border-foreground/30 px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground disabled:opacity-50"
              >
                <LocateFixed className="h-3.5 w-3.5" />
                {t("home.nearMe")}
              </button>
              {user && favourites.length > 0 && (
                <button
                  type="button"
                  aria-pressed={myStationsOnly}
                  onClick={() => setMyStationsOnly((v) => !v)}
                  className={cn(
                    "label-caps inline-flex items-center gap-1.5 border-2 px-3 py-1.5 text-xs",
                    myStationsOnly
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-foreground/30 text-muted-foreground"
                  )}
                >
                  <Star className="h-3.5 w-3.5" />
                  {t("home.myStations")}
                </button>
              )}
              <button
                type="button"
                aria-pressed={openOnly}
                onClick={() => setOpenOnly((v) => !v)}
                className={cn(
                  "label-caps border-2 px-3 py-1.5 text-xs",
                  openOnly
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-foreground/30 text-muted-foreground"
                )}
              >
                {t("home.openOnly")}
              </button>
              <select
                aria-label={t("home.allCategories")}
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="h-8 min-w-0 max-w-full border-2 border-foreground/30 bg-card px-2 text-xs"
              >
                <option value="">{t("home.allCategories")}</option>
                {(categoriesData?.data ?? []).map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="relative">
              <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder={t("home.search")}
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
