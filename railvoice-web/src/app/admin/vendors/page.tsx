"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Briefcase, AlertTriangle, CheckCircle, FileText, Loader2, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { VendorScorecardResponse } from "@/lib/types";

export default function VendorsPage() {
  const queryClient = useQueryClient();
  const [triggering, setTriggering] = useState(false);

  const { data, isLoading } = useQuery<VendorScorecardResponse>({
    queryKey: ["vendors_scorecard"],
    queryFn: () => api.vendors.getScorecard(),
    refetchInterval: 10000,
  });

  const triggerEngine = async () => {
    try {
      setTriggering(true);
      const res = await api.vendors.triggerEngine();
      toast.success(`Penalty Engine triggered successfully. Created ${res.penalty_notes_created} notes.`);
      queryClient.invalidateQueries({ queryKey: ["vendors_scorecard"] });
    } catch (e: any) {
      toast.error(e.message || "Failed to trigger engine");
    } finally {
      setTriggering(false);
    }
  };

  const approveMutation = useMutation({
    mutationFn: (id: string) => api.vendors.approvePenalty(id),
    onSuccess: () => {
      toast.success("Penalty Note Approved");
      queryClient.invalidateQueries({ queryKey: ["vendors_scorecard"] });
    },
    onError: (e: any) => {
      toast.error(e.message || "Failed to approve penalty note");
    }
  });

  return (
    <main className="flex-1 overflow-y-auto p-4 lg:p-8">
      <div className="mx-auto max-w-7xl space-y-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <PageHeader
            title="Vendor Performance & Penalty Engine"
            description="Monitor contractor SLA compliance and manage automated penalty deductions."
          />
          <Button
            onClick={triggerEngine}
            disabled={triggering}
            className="shrink-0 gap-2 bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/20"
          >
            {triggering ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            Trigger Daily Penalty Calculation
          </Button>
        </div>

        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-48 rounded-xl" />
            ))}
          </div>
        ) : !data || data.items.length === 0 ? (
          <Card className="flex flex-col items-center justify-center p-12 text-center border-dashed">
            <div className="rounded-full bg-muted p-4 mb-4">
              <Briefcase className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold">No active vendor contracts found</h3>
            <p className="text-muted-foreground max-w-md mt-2">
              Vendor contracts and their performance metrics will appear here once configured in the database.
            </p>
          </Card>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {data.items.map((item) => (
              <Card
                key={item.contract.id}
                className={cn(
                  "overflow-hidden transition-all duration-300 hover:shadow-lg border",
                  item.pending_penalties > 0
                    ? "border-amber-500/50 shadow-amber-500/10"
                    : "border-border hover:border-indigo-500/30"
                )}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-lg">{item.contract.vendor_name}</h3>
                      <p className="text-sm font-medium text-muted-foreground font-mono">
                        {item.contract.contract_code}
                      </p>
                    </div>
                    {item.pending_penalties > 0 ? (
                      <div className="rounded-full bg-amber-500/10 p-2 text-amber-500 ring-1 ring-amber-500/20">
                        <AlertTriangle className="h-5 w-5" />
                      </div>
                    ) : (
                      <div className="rounded-full bg-emerald-500/10 p-2 text-emerald-500 ring-1 ring-emerald-500/20">
                        <CheckCircle className="h-5 w-5" />
                      </div>
                    )}
                  </div>

                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4 rounded-lg bg-muted/50 p-4">
                      <div>
                        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                          SLA Breaches
                        </p>
                        <p className="text-2xl font-bold font-mono">
                          {item.sla_breaches_count}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                          Resolved
                        </p>
                        <p className="text-2xl font-bold font-mono text-emerald-500">
                          {item.resolved_issues_count}
                        </p>
                      </div>
                    </div>

                    <div className="space-y-2 border-t border-border pt-4">
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-muted-foreground">Total Deducted</span>
                        <span className="font-mono font-semibold text-rose-500">
                          ₹{Number(item.total_penalty_deducted).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-muted-foreground">Pending Approval</span>
                        <span className="font-mono font-semibold text-amber-500">
                          ₹{Number(item.pending_penalties).toLocaleString()}
                        </span>
                      </div>
                    </div>
                    
                    <div className="pt-2">
                      <Button variant="outline" className="w-full text-xs" onClick={() => {
                        toast.info("Detailed ledger view not implemented yet.");
                      }}>
                        <FileText className="h-4 w-4 mr-2" />
                        View Penalty Ledger
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
