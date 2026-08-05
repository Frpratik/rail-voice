"use client";

import dynamic from "next/dynamic";
import { useQuery } from "@tanstack/react-query";
import { Activity, ShieldAlert, CheckCircle2, AlertTriangle, RefreshCw } from "lucide-react";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { StationHeatmapResponse } from "@/lib/types";

// Dynamic import for Leaflet map component to prevent SSR window reference error
const StationHeatmapMap = dynamic(
  () => import("@/components/admin/station-heatmap-map"),
  {
    ssr: false,
    loading: () => <Skeleton className="h-[600px] w-full rounded-2xl" />,
  }
);

export default function HeatmapAnalyticsPage() {
  const { data, isLoading, refetch, isRefetching } = useQuery<StationHeatmapResponse>({
    queryKey: ["station_heatmap"],
    queryFn: () => api.analytics.getStationHeatmap(),
    refetchInterval: 15000,
  });

  const features = data?.features || [];

  const totalStations = features.length;
  const criticalStations = features.filter((f) => f.properties.health_score < 50).length;
  const warningStations = features.filter((f) => f.properties.health_score >= 50 && f.properties.health_score < 80).length;
  const healthyStations = features.filter((f) => f.properties.health_score >= 80).length;

  return (
    <main className="flex-1 overflow-y-auto p-4 lg:p-8">
      <div className="mx-auto max-w-7xl space-y-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <PageHeader
            title="Station Amenity & Infrastructure Heatmap"
            description="Geospatial corridor intelligence displaying live Station Health Indices across platforms and passenger amenities."
          />
          <Button
            onClick={() => refetch()}
            disabled={isRefetching}
            variant="outline"
            className="shrink-0 gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isRefetching ? "animate-spin" : ""}`} />
            Refresh Corridor Data
          </Button>
        </div>

        {/* Stats Grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="p-5 flex items-center gap-4">
            <div className="rounded-xl bg-indigo-500/10 p-3 text-indigo-500">
              <Activity className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Total Stations
              </p>
              <p className="text-2xl font-bold font-mono">{totalStations}</p>
            </div>
          </Card>

          <Card className="p-5 flex items-center gap-4 border-emerald-500/30">
            <div className="rounded-xl bg-emerald-500/10 p-3 text-emerald-500">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Healthy (&gt;80 Score)
              </p>
              <p className="text-2xl font-bold font-mono text-emerald-500">{healthyStations}</p>
            </div>
          </Card>

          <Card className="p-5 flex items-center gap-4 border-amber-500/30">
            <div className="rounded-xl bg-amber-500/10 p-3 text-amber-500">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Moderate Risk (50-79)
              </p>
              <p className="text-2xl font-bold font-mono text-amber-500">{warningStations}</p>
            </div>
          </Card>

          <Card className="p-5 flex items-center gap-4 border-rose-500/30">
            <div className="rounded-xl bg-rose-500/10 p-3 text-rose-500">
              <ShieldAlert className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Critical (&lt;50 Score)
              </p>
              <p className="text-2xl font-bold font-mono text-rose-500">{criticalStations}</p>
            </div>
          </Card>
        </div>

        {/* Heatmap Map Container */}
        {isLoading ? (
          <Skeleton className="h-[600px] w-full rounded-2xl" />
        ) : (
          <StationHeatmapMap features={features} />
        )}
      </div>
    </main>
  );
}
