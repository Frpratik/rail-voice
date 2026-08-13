"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { toast } from "sonner";
import { AlertTriangle, ArrowUpRight, CheckCircle2, Flame, ShieldAlert, UserCheck } from "lucide-react";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Label, Textarea } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";

export default function AdminIssuesPage() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [remarks, setRemarks] = useState("");
  const [newStatus, setNewStatus] = useState("verified");
  const [assigneeId, setAssigneeId] = useState("");
  const [escalateTarget, setEscalateTarget] = useState<"station_manager" | "division" | "zone">(
    "division"
  );
  const [statusFilter, setStatusFilter] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-issues", statusFilter],
    queryFn: () => api.admin.issues({ status_filter: statusFilter || undefined }),
    retry: false,
  });

  const { data: officersData } = useQuery({
    queryKey: ["admin-officers"],
    queryFn: () => api.admin.officers(),
    retry: false,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["admin-issues"] });
    setSelectedId(null);
    setRemarks("");
  };

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      status,
      remarks,
    }: {
      id: string;
      status: string;
      remarks: string;
    }) => api.admin.updateStatus(id, { status, remarks }),
    onSuccess: () => {
      toast.success("Grievance status updated successfully");
      invalidate();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const assignMutation = useMutation({
    mutationFn: () =>
      api.admin.assign(selectedId!, { assignee_id: assigneeId, remarks }),
    onSuccess: () => {
      toast.success("Duty staff assigned to issue");
      invalidate();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const escalateMutation = useMutation({
    mutationFn: () =>
      api.admin.escalate(selectedId!, { target: escalateTarget, remarks }),
    onSuccess: () => {
      toast.success("Grievance escalated to Western Railway Authority");
      invalidate();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const issues = data?.data.items ?? [];
  const officers = officersData?.data.items ?? [];
  const selected = issues.find((i) => i.id === selectedId);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Triage & Operations"
        title="Issue Triage Queue"
        description="Review incoming citizen reports, verify on-ground conditions, assign staff, or escalate to Divisional Headquarters."
      />

      {/* Filter Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {[
          { value: "", label: "All Grievances" },
          { value: "submitted", label: "Pending Review" },
          { value: "verified", label: "Verified" },
          { value: "action_started", label: "Action Started" },
          { value: "forwarded_division", label: "Escalated" },
          { value: "completed", label: "Resolved" },
        ].map((tab) => (
          <button
            key={tab.value}
            type="button"
            onClick={() => {
              setStatusFilter(tab.value);
              setSelectedId(null);
            }}
            className={`shrink-0 rounded-full px-3.5 py-1.5 text-xs font-semibold tracking-tight transition-all ${
              statusFilter === tab.value
                ? "bg-primary text-primary-foreground shadow-sm"
                : "bg-card text-muted-foreground ring-1 ring-card-border hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <Card className="overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr className="border-b border-card-border bg-muted/40 text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                <th className="px-5 py-3.5">Upvotes</th>
                <th className="px-5 py-3.5">Grievance</th>
                <th className="px-5 py-3.5">Station</th>
                <th className="px-5 py-3.5">Category</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5">Reported</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-muted-foreground">
                    Loading station triage queue…
                  </td>
                </tr>
              )}
              {!isLoading && issues.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-muted-foreground">
                    No grievances found in this filter.
                  </td>
                </tr>
              )}
              {issues.map((issue) => (
                <tr
                  key={issue.id}
                  className={`cursor-pointer border-b border-card-border transition-colors hover:bg-muted/30 ${
                    selectedId === issue.id ? "bg-accent/10" : ""
                  }`}
                  onClick={() => setSelectedId(issue.id)}
                >
                  <td className="px-5 py-4">
                    <span className="inline-flex items-center gap-1 font-bold text-accent text-xs">
                      <Flame className="h-3.5 w-3.5" />
                      {issue.support_count}
                    </span>
                  </td>
                  <td className="max-w-xs truncate px-5 py-4 font-medium tracking-tight">
                    <div className="flex items-center gap-1.5">
                      {issue.is_emergency && (
                        <AlertTriangle className="h-3.5 w-3.5 text-destructive shrink-0" />
                      )}
                      <span className="truncate">{issue.title ?? issue.description}</span>
                    </div>
                    <span className="block font-mono text-[10px] text-muted-foreground">
                      {issue.issue_number}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-xs">{issue.location.station.name}</td>
                  <td className="px-5 py-4 text-xs text-muted-foreground">
                    {issue.category?.name ?? "General"}
                  </td>
                  <td className="px-5 py-4">
                    <StatusBadge status={issue.status} />
                  </td>
                  <td className="px-5 py-4 text-xs text-muted-foreground">
                    {formatRelativeTime(issue.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Selected Issue Action Drawer */}
      <AnimatePresence>
        {selected && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
          >
            <Card elevated className="space-y-5 p-6 border-accent/40 bg-card">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-mono text-xs text-muted-foreground uppercase">
                    Triage Actions for {selected.issue_number}
                  </p>
                  <h3 className="text-display mt-1 text-lg font-semibold tracking-tight">
                    {selected.title ?? "Citizen Grievance"}
                  </h3>
                  <p className="text-xs text-muted-foreground mt-1 max-w-xl">
                    {selected.description}
                  </p>
                </div>
                <Link
                  href={`/issues/${selected.id}`}
                  target="_blank"
                  className="inline-flex items-center gap-1 text-xs font-semibold text-accent hover:underline"
                >
                  Open public ticket <ArrowUpRight className="h-3.5 w-3.5" />
                </Link>
              </div>

              <div className="grid gap-6 md:grid-cols-3 pt-2">
                {/* 1. Update Status */}
                <div className="space-y-3 rounded-2xl border border-card-border bg-background p-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-accent" />
                    <h4 className="text-xs font-bold uppercase tracking-wider">
                      Update Lifecycle Status
                    </h4>
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="status">New Status</Label>
                    <select
                      id="status"
                      value={newStatus}
                      onChange={(e) => setNewStatus(e.target.value)}
                      className="w-full h-9 rounded-xl border border-card-border bg-card px-3 text-xs"
                    >
                      <option value="verified">Verified (Confirmed on-ground)</option>
                      <option value="action_started">Action Started (In Progress)</option>
                      <option value="work_in_progress">Work in Progress</option>
                      <option value="completed">Completed / Resolved</option>
                      <option value="rejected">Rejected (Out of scope)</option>
                    </select>
                  </div>
                  <Button
                    size="sm"
                    variant="accent"
                    disabled={updateMutation.isPending || !remarks.trim()}
                    onClick={() =>
                      updateMutation.mutate({
                        id: selected.id,
                        status: newStatus,
                        remarks: remarks.trim(),
                      })
                    }
                    className="w-full"
                  >
                    {updateMutation.isPending ? "Updating..." : "Update Status"}
                  </Button>
                </div>

                {/* 2. Assign Duty Staff */}
                <div className="space-y-3 rounded-2xl border border-card-border bg-background p-4">
                  <div className="flex items-center gap-2">
                    <UserCheck className="h-4 w-4 text-accent" />
                    <h4 className="text-xs font-bold uppercase tracking-wider">
                      Assign Duty Staff
                    </h4>
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="assignee">Responsible Official</Label>
                    <select
                      id="assignee"
                      value={assigneeId}
                      onChange={(e) => setAssigneeId(e.target.value)}
                      className="w-full h-9 rounded-xl border border-card-border bg-card px-3 text-xs"
                    >
                      <option value="">Select official / supervisor</option>
                      {officers.map((o) => (
                        <option key={o.id} value={o.id}>
                          {o.display_name} ({o.roles.join(", ")})
                        </option>
                      ))}
                    </select>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={assignMutation.isPending || !assigneeId || !remarks.trim()}
                    onClick={() => assignMutation.mutate()}
                    className="w-full"
                  >
                    {assignMutation.isPending ? "Assigning..." : "Assign Official"}
                  </Button>
                </div>

                {/* 3. Escalate to WR Authority */}
                <div className="space-y-3 rounded-2xl border border-card-border bg-background p-4">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4 text-warning" />
                    <h4 className="text-xs font-bold uppercase tracking-wider">
                      Escalate to WR Authority
                    </h4>
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="escalate">Escalate Destination</Label>
                    <select
                      id="escalate"
                      value={escalateTarget}
                      onChange={(e) =>
                        setEscalateTarget(
                          e.target.value as "station_manager" | "division" | "zone"
                        )
                      }
                      className="w-full h-9 rounded-xl border border-card-border bg-card px-3 text-xs"
                    >
                      <option value="division">Divisional Office (Mumbai MUM)</option>
                      <option value="zone">Zone Headquarters (Churchgate WR)</option>
                    </select>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={escalateMutation.isPending || !remarks.trim()}
                    onClick={() => escalateMutation.mutate()}
                    className="w-full border-warning/40 text-warning hover:bg-warning/10"
                  >
                    {escalateMutation.isPending ? "Escalating..." : "Escalate Report"}
                  </Button>
                </div>
              </div>

              {/* Action Remarks */}
              <div className="space-y-1.5 pt-1">
                <Label htmlFor="remarks">Operational Action Remarks * (Required for audit timeline)</Label>
                <Textarea
                  id="remarks"
                  rows={2}
                  placeholder="State the verification findings, work order number, or reason for status transition / escalation..."
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  className="text-xs"
                />
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
