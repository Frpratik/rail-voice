"use client";

import * as React from "react";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Zap,
  Users,
  Wrench,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  Clock,
  UserCheck,
  Phone,
  Building2,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/ui/empty-state";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function AdminDispatchPage() {
  const queryClient = useQueryClient();
  const [dispatching, setDispatching] = useState(false);

  // Queries
  const { data: roster, isLoading: rosterLoading, refetch: refetchRoster } = useQuery({
    queryKey: ["dispatch_roster"],
    queryFn: () => api.dispatch.getRoster(),
  });

  const { data: recommendations, isLoading: recsLoading, refetch: refetchRecs } = useQuery({
    queryKey: ["dispatch_recommendations"],
    queryFn: () => api.dispatch.getRecommendations(),
  });

  // Mutation
  const autoAssignMutation = useMutation({
    mutationFn: () => api.dispatch.autoAssign(),
    onMutate: () => setDispatching(true),
    onSuccess: (data) => {
      toast.success(`⚡ AI Dispatch Complete! Dispatched ${data.dispatched_count} maintenance staff to active grievances.`);
      void queryClient.invalidateQueries({ queryKey: ["dispatch_roster"] });
      void queryClient.invalidateQueries({ queryKey: ["dispatch_recommendations"] });
    },
    onError: (err: unknown) => {
      toast.error(err instanceof Error ? err.message : "Auto-dispatch failed");
    },
    onSettled: () => setDispatching(false),
  });

  const skillBadges: Record<string, { label: string; bg: string; text: string }> = {
    housekeeping: { label: "Housekeeping", bg: "bg-emerald-500/10 border-emerald-500/30", text: "text-emerald-500" },
    electrical: { label: "Electrical", bg: "bg-amber-500/10 border-amber-500/30", text: "text-amber-500" },
    mechanical: { label: "Mechanical", bg: "bg-blue-500/10 border-blue-500/30", text: "text-blue-500" },
    safety: { label: "RPF Safety", bg: "bg-rose-500/10 border-rose-500/30", text: "text-rose-500" },
  };

  const statusPills: Record<string, { label: string; color: string }> = {
    available: { label: "Available", color: "bg-emerald-500" },
    on_task: { label: "On Task", color: "bg-amber-500" },
    off_duty: { label: "Off Duty", color: "bg-muted-foreground" },
  };

  return (
    <main className="flex-1 overflow-y-auto p-4 lg:p-8">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Page Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <PageHeader
            title="AI Dynamic Workforce Dispatch & Resource Allocator"
            description="Smart workforce routing matching open grievances with qualified station personnel, skill categories, and station proximity."
          />
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                void refetchRoster();
                void refetchRecs();
              }}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button
              className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-semibold shadow-lg shadow-amber-500/20"
              disabled={dispatching || autoAssignMutation.isPending || !recommendations?.length}
              onClick={() => autoAssignMutation.mutate()}
            >
              <Zap className={`h-4 w-4 mr-2 ${dispatching ? "animate-spin" : ""}`} />
              {dispatching ? "Dispatching Staff..." : "1-Click Auto-Dispatch Staff"}
            </Button>
          </div>
        </div>

        {/* Top Summary Metrics */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="p-5 border-border/50 bg-card/60 backdrop-blur-sm">
            <div className="flex flex-row items-center justify-between pb-2">
              <h3 className="text-sm font-medium text-muted-foreground">Active Workforce</h3>
              <Users className="h-4 w-4 text-blue-500" />
            </div>
            <div>
              <div className="text-2xl font-bold font-mono">{roster?.total_staff || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Personnel across Division Stations</p>
            </div>
          </Card>

          <Card className="p-5 border-border/50 bg-card/60 backdrop-blur-sm">
            <div className="flex flex-row items-center justify-between pb-2">
              <h3 className="text-sm font-medium text-muted-foreground">Available Personnel</h3>
              <UserCheck className="h-4 w-4 text-emerald-500" />
            </div>
            <div>
              <div className="text-2xl font-bold font-mono text-emerald-500">{roster?.available_count || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Ready for instant assignment</p>
            </div>
          </Card>

          <Card className="p-5 border-border/50 bg-card/60 backdrop-blur-sm">
            <div className="flex flex-row items-center justify-between pb-2">
              <h3 className="text-sm font-medium text-muted-foreground">Dispatched On Task</h3>
              <Wrench className="h-4 w-4 text-amber-500" />
            </div>
            <div>
              <div className="text-2xl font-bold font-mono text-amber-500">{roster?.on_task_count || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Currently resolving grievances</p>
            </div>
          </Card>

          <Card className="p-5 border-border/50 bg-card/60 backdrop-blur-sm">
            <div className="flex flex-row items-center justify-between pb-2">
              <h3 className="text-sm font-medium text-muted-foreground">Pending Recommendations</h3>
              <Sparkles className="h-4 w-4 text-orange-500" />
            </div>
            <div>
              <div className="text-2xl font-bold font-mono text-orange-500">{recommendations?.length || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">Optimal staff-to-issue pairs</p>
            </div>
          </Card>
        </div>

        {/* Skill Matrix Category Distribution */}
        <Card className="p-6 border-border/50 bg-card/60 backdrop-blur-sm">
          <div className="mb-4">
            <h3 className="text-base font-semibold flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-indigo-500" />
              Division Skill & Department Capacity Matrix
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">Real-time headcount grouped by maintenance expertise and RPF safety team</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
            {Object.entries(skillBadges).map(([key, cfg]) => {
              const count = roster?.category_counts?.[key] || 0;
              return (
                <div key={key} className={`rounded-xl border p-4 ${cfg.bg} transition-colors`}>
                  <div className="flex justify-between items-center mb-2">
                    <span className={`text-xs font-semibold uppercase tracking-wider ${cfg.text}`}>{cfg.label}</span>
                    <span className={`text-xl font-bold font-mono ${cfg.text}`}>{count}</span>
                  </div>
                  <div className="w-full bg-background/50 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full ${cfg.text.replace("text-", "bg-")}`}
                      style={{ width: `${Math.min(100, (count / (roster?.total_staff || 1)) * 100 * 3)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* AI Recommendations Queue */}
        <Card className="p-6 border-border/50 bg-card/60 backdrop-blur-sm">
          <div className="flex flex-row items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-amber-500" />
                AI Smart Dispatch Recommendation Queue
              </h3>
              <p className="text-xs text-muted-foreground mt-0.5">Intelligent staff-to-issue routing suggestions powered by skill matching and priority scores</p>
            </div>
            <Badge variant="outline" className="font-mono text-xs border-amber-500/30 text-amber-500">
              {recommendations?.length || 0} Matches Found
            </Badge>
          </div>
          <div>
            {recsLoading ? (
              <div className="py-8 text-center text-sm text-muted-foreground">Loading AI recommendations...</div>
            ) : !recommendations || recommendations.length === 0 ? (
              <div className="py-8 text-center text-sm text-muted-foreground flex flex-col items-center gap-2">
                <CheckCircle2 className="h-8 w-8 text-emerald-500 mb-1" />
                <span>All open grievances have assigned personnel or no unassigned high-priority tickets remain!</span>
              </div>
            ) : (
              <div className="space-y-4">
                {recommendations.map((rec) => {
                  const cfg = skillBadges[rec.recommended_staff.skill_category] || skillBadges.housekeeping;
                  return (
                    <motion.div
                      key={rec.issue_id}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl border border-border/60 bg-background/40 hover:bg-background/80 transition-all"
                    >
                      <div className="space-y-1.5 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-muted">
                            {rec.issue_number}
                          </span>
                          <span className="font-semibold text-sm">{rec.title || rec.category_name}</span>
                          <Badge variant="outline" className="text-xs border-blue-500/30 text-blue-500">
                            <Building2 className="h-3 w-3 mr-1" />
                            {rec.station_name}
                          </Badge>
                          <Badge variant="outline" className="text-xs border-orange-500/30 text-orange-500 font-mono">
                            <TrendingUp className="h-3 w-3 mr-1" />
                            Priority {(rec.priority_score ?? 0).toFixed(0)}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">{rec.reason}</p>
                      </div>

                      <div className="flex items-center gap-4 border-t md:border-t-0 md:border-l border-border pt-3 md:pt-0 md:pl-4">
                        <div className="text-left md:text-right">
                          <div className="flex items-center gap-2 justify-start md:justify-end">
                            <span className="font-semibold text-sm">{rec.recommended_staff.full_name}</span>
                            <Badge variant="outline" className={`text-xs ${cfg.bg} ${cfg.text}`}>
                              {cfg.label}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2 mt-1 justify-start md:justify-end">
                            <span className="text-xs text-emerald-500 font-mono font-medium">
                              ⚡ {rec.confidence_score}% Match Confidence
                            </span>
                          </div>
                        </div>

                        <Button
                          size="sm"
                          variant="secondary"
                          className="bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 border border-amber-500/30 text-xs shrink-0"
                          disabled={autoAssignMutation.isPending}
                          onClick={() => autoAssignMutation.mutate()}
                        >
                          <ArrowRight className="h-3.5 w-3.5 mr-1" />
                          Dispatch
                        </Button>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>
        </Card>

        {/* Live Workforce Personnel Roster */}
        <Card className="p-6 border-border/50 bg-card/60 backdrop-blur-sm">
          <div className="mb-4">
            <h3 className="text-base font-semibold flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-500" />
              Active Station Workforce Roster
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">Complete duty roster across division stations, shift schedules, and mobile contacts</p>
          </div>
          <div>
            {rosterLoading ? (
              <div className="py-8 text-center text-sm text-muted-foreground">Loading workforce roster...</div>
            ) : !roster?.staff_list.length ? (
              <div className="py-8 text-center text-sm text-muted-foreground">No workforce personnel registered.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-border text-xs uppercase text-muted-foreground">
                      <th className="py-3 px-4 font-medium">Personnel Name</th>
                      <th className="py-3 px-4 font-medium">Department Skill</th>
                      <th className="py-3 px-4 font-medium">Status</th>
                      <th className="py-3 px-4 font-medium">Shift Timing</th>
                      <th className="py-3 px-4 font-medium">Contact Number</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40 font-mono text-xs">
                    {roster.staff_list.map((staff) => {
                      const cfg = skillBadges[staff.skill_category] || skillBadges.housekeeping;
                      const st = statusPills[staff.status] || statusPills.available;
                      return (
                        <tr key={staff.id} className="hover:bg-muted/30 transition-colors">
                          <td className="py-3.5 px-4 font-sans font-medium text-foreground">{staff.full_name}</td>
                          <td className="py-3.5 px-4">
                            <Badge variant="outline" className={`text-xs ${cfg.bg} ${cfg.text}`}>
                              {cfg.label}
                            </Badge>
                          </td>
                          <td className="py-3.5 px-4">
                            <div className="flex items-center gap-2">
                              <span className={`h-2 w-2 rounded-full ${st.color}`} />
                              <span className="font-sans font-medium text-xs">{st.label}</span>
                            </div>
                          </td>
                          <td className="py-3.5 px-4 text-muted-foreground">
                            <Clock className="h-3.5 w-3.5 inline mr-1 text-muted-foreground" />
                            {staff.shift_start || "08:00"} - {staff.shift_end || "16:00"}
                          </td>
                          <td className="py-3.5 px-4 text-muted-foreground">
                            <Phone className="h-3.5 w-3.5 inline mr-1 text-muted-foreground" />
                            {staff.contact_number || "+91 98200 00000"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </Card>
      </div>
    </main>
  );
}
