"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { toast } from "sonner";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Label, Select, Textarea } from "@/components/ui/input";
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
  const [mergeIds, setMergeIds] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-issues"],
    queryFn: () => api.admin.issues(),
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
    setMergeIds("");
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
      toast.success("Status updated");
      invalidate();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const assignMutation = useMutation({
    mutationFn: () =>
      api.admin.assign(selectedId!, { assignee_id: assigneeId, remarks }),
    onSuccess: () => {
      toast.success("Issue assigned");
      invalidate();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const escalateMutation = useMutation({
    mutationFn: () =>
      api.admin.escalate(selectedId!, { target: escalateTarget, remarks }),
    onSuccess: () => {
      toast.success("Issue escalated");
      invalidate();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const mergeMutation = useMutation({
    mutationFn: () => {
      const duplicate_ids = mergeIds
        .split(/[\s,]+/)
        .map((s) => s.trim())
        .filter(Boolean);
      return api.admin.merge(selectedId!, { duplicate_ids, remarks });
    },
    onSuccess: () => {
      toast.success("Duplicates merged into primary");
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
        eyebrow="Triage"
        title="Issue queue"
        description="Prioritized work list with lifecycle, assignment, and escalation."
      />

      <Card className="overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr className="border-b border-card-border bg-muted/40 text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                <th className="px-5 py-3.5">Priority</th>
                <th className="px-5 py-3.5">Issue</th>
                <th className="px-5 py-3.5">Station</th>
                <th className="px-5 py-3.5">Supports</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5">Age</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-muted-foreground">
                    Loading queue…
                  </td>
                </tr>
              )}
              {!isLoading && issues.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-muted-foreground">
                    No issues in queue.
                  </td>
                </tr>
              )}
              {issues.map((issue) => (
                <tr
                  key={issue.id}
                  className={`cursor-pointer border-b border-card-border transition-colors hover:bg-muted/30 ${
                    selectedId === issue.id ? "bg-accent/5" : ""
                  }`}
                  onClick={() => setSelectedId(issue.id)}
                >
                  <td className="px-5 py-4 font-mono text-xs font-semibold">
                    {issue.priority_score.toFixed(1)}
                  </td>
                  <td className="max-w-xs truncate px-5 py-4 font-medium tracking-tight">
                    <Link
                      href={`/issues/${issue.id}`}
                      className="hover:text-accent"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {issue.title ?? issue.description.slice(0, 48)}
                    </Link>
                  </td>
                  <td className="px-5 py-4">
                    <span className="rounded-md bg-muted px-2 py-0.5 font-mono text-xs">
                      {issue.location.station.code}
                    </span>
                  </td>
                  <td className="px-5 py-4">{issue.support_count}</td>
                  <td className="px-5 py-4">
                    <StatusBadge status={issue.status} />
                  </td>
                  <td className="px-5 py-4 text-muted-foreground">
                    {formatRelativeTime(issue.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <AnimatePresence>
        {selectedId && selected && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="grid gap-4 lg:grid-cols-3"
          >
            <Card elevated className="space-y-4 p-6 lg:col-span-1">
              <div>
                <p className="font-mono text-xs text-muted-foreground">
                  {selected.issue_number}
                </p>
                <h2 className="mt-1 text-display text-lg font-semibold tracking-tight">
                  Update status
                </h2>
              </div>
              <div>
                <Label htmlFor="status">New status</Label>
                <Select
                  id="status"
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                >
                  <option value="verified">Verified</option>
                  <option value="assigned">Assigned</option>
                  <option value="work_in_progress">Work in progress</option>
                  <option value="completed">Completed</option>
                  <option value="closed">Closed</option>
                  <option value="rejected">Rejected</option>
                </Select>
              </div>
              <div>
                <Label htmlFor="remarks">Remarks (required)</Label>
                <Textarea
                  id="remarks"
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  placeholder="Audit trail note — what changed and why"
                />
              </div>
              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setSelectedId(null)}>
                  Cancel
                </Button>
                <Button
                  variant="accent"
                  disabled={remarks.length < 5 || updateMutation.isPending}
                  onClick={() =>
                    updateMutation.mutate({
                      id: selectedId,
                      status: newStatus,
                      remarks,
                    })
                  }
                >
                  Save update
                </Button>
              </div>
            </Card>

            <Card elevated className="space-y-4 p-6">
              <h2 className="text-display text-lg font-semibold tracking-tight">Assign</h2>
              <div>
                <Label htmlFor="assignee">Officer</Label>
                <Select
                  id="assignee"
                  value={assigneeId}
                  onChange={(e) => setAssigneeId(e.target.value)}
                >
                  <option value="">Select officer</option>
                  {officers.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.display_name} ({o.roles[0]})
                    </option>
                  ))}
                </Select>
              </div>
              <Button
                variant="accent"
                className="w-full"
                disabled={
                  !assigneeId || remarks.length < 5 || assignMutation.isPending
                }
                onClick={() => assignMutation.mutate()}
              >
                Assign officer
              </Button>
              {officers.length === 0 && (
                <p className="text-xs text-muted-foreground">
                  No officials with roles found yet — seed/admin users appear here.
                </p>
              )}
            </Card>

            <Card elevated className="space-y-4 p-6">
              <h2 className="text-display text-lg font-semibold tracking-tight">Escalate</h2>
              <div>
                <Label htmlFor="escalate">Escalate to</Label>
                <Select
                  id="escalate"
                  value={escalateTarget}
                  onChange={(e) =>
                    setEscalateTarget(
                      e.target.value as "station_manager" | "division" | "zone"
                    )
                  }
                >
                  <option value="station_manager">Station manager</option>
                  <option value="division">Division</option>
                  <option value="zone">Zone</option>
                </Select>
              </div>
              <Button
                className="w-full"
                disabled={remarks.length < 5 || escalateMutation.isPending}
                onClick={() => escalateMutation.mutate()}
              >
                Escalate
              </Button>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {selectedId && selected && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <Card elevated className="space-y-4 p-6">
              <div>
                <h2 className="text-display text-lg font-semibold tracking-tight">
                  Merge duplicates
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Keep this issue as primary. Paste other issue UUIDs (comma or space
                  separated) to fold them in and transfer unique supports.
                </p>
              </div>
              <div>
                <Label htmlFor="mergeIds">Duplicate issue IDs</Label>
                <Textarea
                  id="mergeIds"
                  value={mergeIds}
                  onChange={(e) => setMergeIds(e.target.value)}
                  placeholder="uuid-1, uuid-2"
                />
              </div>
              <Button
                variant="accent"
                disabled={
                  mergeIds.trim().length < 8 ||
                  remarks.length < 5 ||
                  mergeMutation.isPending
                }
                onClick={() => mergeMutation.mutate()}
              >
                Merge into {selected.issue_number}
              </Button>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
