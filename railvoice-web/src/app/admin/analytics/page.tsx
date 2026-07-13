"use client";

import { BarChart3, Map } from "lucide-react";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/empty-state";

export default function AdminAnalyticsPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Insights"
        title="Analytics"
        description="Heatmaps and station performance — roadmap for the next ops release."
      />

      <div className="grid gap-4 md:grid-cols-2">
        <Card elevated className="flex min-h-[220px] flex-col items-center justify-center gap-3 p-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
            <Map className="h-5 w-5" />
          </div>
          <h3 className="font-semibold tracking-tight">Station heatmaps</h3>
          <p className="max-w-xs text-sm text-muted-foreground">
            Interactive density overlays by platform and category are coming next.
          </p>
        </Card>
        <Card elevated className="flex min-h-[220px] flex-col items-center justify-center gap-3 p-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
            <BarChart3 className="h-5 w-5" />
          </div>
          <h3 className="font-semibold tracking-tight">Resolution charts</h3>
          <p className="max-w-xs text-sm text-muted-foreground">
            Trend lines for resolved vs pending and average resolution time.
          </p>
        </Card>
      </div>
    </div>
  );
}
