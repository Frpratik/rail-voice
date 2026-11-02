"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Inbox, Printer, Share2, Star } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { useState } from "react";
import { toast } from "sonner";
import { StationSummary } from "@/components/ai/station-summary";
import { IssueCard } from "@/components/issues/issue-card";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState, PageHeader } from "@/components/ui/empty-state";
import { IssueCardSkeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

export default function StationPage() {
  const { code } = useParams<{ code: string }>();
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const [showPoster, setShowPoster] = useState(false);

  const { data: stationData } = useQuery({
    queryKey: ["station", code],
    queryFn: () => api.stations.get(code),
    enabled: !!code,
  });

  const { data: statsData } = useQuery({
    queryKey: ["station-stats", code],
    queryFn: () => api.stations.stats(code),
    enabled: !!code,
  });

  const { data: favouritesData } = useQuery({
    queryKey: ["favourites"],
    queryFn: () => api.me.favourites(),
    enabled: !!user,
  });

  const { data: issuesData, isLoading } = useQuery({
    queryKey: ["issues", "station", code],
    queryFn: () => api.issues.list({ station_code: code, limit: 30 }),
    enabled: !!code,
  });

  const station = stationData?.data;
  const stats = statsData?.data;
  const issues = issuesData?.data.items ?? [];
  const isFavourite = (favouritesData?.data.codes ?? []).includes(code.toUpperCase());

  const favourite = useMutation({
    mutationFn: () => api.stations.favourite(code, !isFavourite),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["favourites"] }),
    onError: (e: Error) => toast.error(e.message),
  });

  const pageUrl = typeof window !== "undefined" ? `${window.location.origin}/stations/${code}` : "";

  const share = async () => {
    const title = `${station?.name ?? code} station on RailVoice`;
    if (navigator.share) {
      await navigator.share({ title, url: pageUrl }).catch(() => undefined);
    } else {
      window.open(`https://wa.me/?text=${encodeURIComponent(`${title}: ${pageUrl}`)}`, "_blank");
    }
  };

  return (
    <div className="space-y-6">
      <Link
        href="/stations"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        All stations
      </Link>

      <PageHeader
        eyebrow={station?.code ?? code}
        title={station?.name ?? code}
        description={`${station?.open_issue_count ?? 0} open issues at this station`}
        action={
          <div className="flex flex-wrap gap-2">
            {user && (
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5"
                disabled={favourite.isPending}
                onClick={() => favourite.mutate()}
              >
                <Star className={`h-3.5 w-3.5 ${isFavourite ? "fill-current" : ""}`} />
                {isFavourite ? "My station" : "Add to my stations"}
              </Button>
            )}
            <Button variant="outline" size="sm" className="gap-1.5" onClick={() => void share()}>
              <Share2 className="h-3.5 w-3.5" /> Share
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => setShowPoster((v) => !v)}
            >
              <Printer className="h-3.5 w-3.5" /> QR poster
            </Button>
          </div>
        }
      />

      {stats && (
        <dl className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {[
            { label: "Open", value: stats.open },
            { label: "Fixed", value: stats.fixed },
            { label: "Fix rate", value: stats.fix_rate != null ? `${stats.fix_rate}%` : "—" },
            {
              label: "Avg. fix",
              value: stats.avg_fix_hours != null ? `${stats.avg_fix_hours} h` : "—",
            },
          ].map((s) => (
            <Card key={s.label} className="p-3 sm:p-4">
              <dd className="font-board text-2xl">{s.value}</dd>
              <dt className="label-caps mt-1 text-xs text-muted-foreground">{s.label}</dt>
            </Card>
          ))}
        </dl>
      )}

      {station && <StationSummary stationId={station.id} />}

      {showPoster && (
        <Card className="space-y-4 p-4 text-center">
          <div className="print-area name-board mx-auto max-w-sm p-6">
            <p className="label-caps text-sm">Western Railway</p>
            <p className="text-display text-4xl uppercase">{station?.name ?? code}</p>
            <p className="mt-2 text-sm">Spotted a problem here? Scan to report it.</p>
            <div className="mt-4 flex justify-center">
              <QRCodeSVG value={pageUrl} size={200} marginSize={2} />
            </div>
            <p className="font-board mt-3 break-all text-xs">{pageUrl}</p>
          </div>
          <Button variant="accent" className="gap-1.5" onClick={() => window.print()}>
            <Printer className="h-4 w-4" /> Print poster
          </Button>
        </Card>
      )}

      <div className="grid gap-4">
        {isLoading &&
          Array.from({ length: 3 }).map((_, i) => <IssueCardSkeleton key={i} />)}
        {!isLoading && issues.length === 0 && (
          <EmptyState
            icon={Inbox}
            title="No issues here yet"
            description="This station looks clear. Report if you spot something that needs attention."
            actionLabel="Report an issue"
            actionHref="/report"
          />
        )}
        {issues.map((issue, i) => (
          <IssueCard key={issue.id} issue={issue} index={i} />
        ))}
      </div>
    </div>
  );
}
