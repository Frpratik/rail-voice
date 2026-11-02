"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { toast } from "sonner";
import {
  AlertTriangle,
  ArrowUpRight,
  Camera,
  CheckCircle2,
  Flame,
  ShieldAlert,
  Sparkles,
  UserCheck,
} from "lucide-react";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Label, Textarea } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/empty-state";
import { FixCheck, TriageSuggestion } from "@/components/ai/staff-assist";
import { api } from "@/lib/api";
import { compressImage } from "@/lib/image";
import type { Issue } from "@/lib/types";
import { formatRelativeTime } from "@/lib/utils";

const TEMPLATES = [
  "Checked on site. The problem is confirmed.",
  "Sent to the responsible department. Work will be scheduled.",
  "Waiting for materials. We'll update this when work restarts.",
  "Work is finished. Please check and confirm it's fixed.",
  "Not a railway matter, so we can't act on this report.",
];

function SlaChip({ issue, now }: { issue: Issue; now: number }) {
  if (!issue.sla_due_at || ["completed", "closed", "verified_complete", "rejected"].includes(issue.status)) {
    return null;
  }
  const hours = Math.round((new Date(issue.sla_due_at).getTime() - now) / 3_600_000);
  return (
    <span
      className={`font-board inline-block px-1.5 py-0.5 text-[11px] ${
        issue.overdue ? "bg-destructive text-white" : "bg-muted text-foreground"
      }`}
    >
      {issue.overdue ? `${Math.abs(hours)}h overdue` : `${hours}h left`}
    </span>
  );
}

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
  const [departmentFilter, setDepartmentFilter] = useState("");
  const [mineOnly, setMineOnly] = useState(false);
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [checked, setChecked] = useState<string[]>([]);
  const [now] = useState(() => Date.now());

  // The dashboard links here with ?focus=<id>; open that report straight away.
  useEffect(() => {
    const focus = new URLSearchParams(window.location.search).get("focus");
    if (!focus) return;
    queueMicrotask(() => setSelectedId(focus));
    setTimeout(
      () => document.getElementById("triage-actions")?.scrollIntoView({ behavior: "smooth" }),
      800
    );
  }, []);
  const [bulkStatus, setBulkStatus] = useState("verified");
  const [bulkRemarks, setBulkRemarks] = useState("");
  const [note, setNote] = useState("");
  const [mergeTarget, setMergeTarget] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-issues", statusFilter, departmentFilter, mineOnly, overdueOnly],
    queryFn: () =>
      api.admin.issues({
        status_filter: statusFilter || undefined,
        department: departmentFilter || undefined,
        assigned_to_me: mineOnly,
        overdue_only: overdueOnly,
      }),
    retry: false,
  });

  const { data: departmentsData } = useQuery({
    queryKey: ["admin-departments"],
    queryFn: () => api.admin.departments(),
    retry: false,
  });
  const departments = departmentsData?.data.items ?? [];

  const { data: detailData } = useQuery({
    queryKey: ["admin-issue-detail", selectedId],
    queryFn: () => api.admin.issueDetail(selectedId!),
    enabled: !!selectedId,
    retry: false,
  });
  const detailPhotos = detailData?.data.issue.photos ?? [];
  const notes = (detailData?.data.timeline ?? []).filter((e) => e.event_type === "internal_note");

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

  const { data: aiStatus } = useQuery({ queryKey: ["ai-status"], queryFn: () => api.ai.status() });
  const [suggesting, setSuggesting] = useState(false);

  const suggestWording = async () => {
    if (!selectedId || remarks.trim().length < 2) {
      toast.error("Type a few quick notes first, e.g. \"cleaner sent, 30 min\"");
      return;
    }
    setSuggesting(true);
    try {
      const res = await api.ai.suggestReply({
        issue_id: selectedId,
        notes: remarks.trim(),
        new_status: newStatus,
      });
      setRemarks(res.data.local ? `${res.data.english}\n\n${res.data.local}` : res.data.english);
    } catch {
      toast.error("Couldn't suggest wording right now");
    } finally {
      setSuggesting(false);
    }
  };

  const refreshDetail = () =>
    queryClient.invalidateQueries({ queryKey: ["admin-issue-detail", selectedId] });

  const noteMutation = useMutation({
    mutationFn: () => api.admin.addNote(selectedId!, note.trim()),
    onSuccess: () => {
      setNote("");
      refreshDetail();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const departmentMutation = useMutation({
    mutationFn: (department: string) => api.admin.setDepartment(selectedId!, department || null),
    onSuccess: () => {
      toast.success("Department updated");
      queryClient.invalidateQueries({ queryKey: ["admin-issues"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const mergeMutation = useMutation({
    mutationFn: () => api.admin.merge(selectedId!, mergeTarget),
    onSuccess: (res) => {
      toast.success(`Merged. ${res.data.backers_added} backers moved across.`);
      setMergeTarget("");
      invalidate();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const bulkMutation = useMutation({
    mutationFn: () =>
      api.admin.bulkStatus({ issue_ids: checked, status: bulkStatus, remarks: bulkRemarks.trim() }),
    onSuccess: (res) => {
      const { updated, skipped } = res.data;
      toast.success(
        `${updated.length} updated${skipped.length ? `, ${skipped.length} skipped (wrong status)` : ""}`
      );
      setChecked([]);
      setBulkRemarks("");
      invalidate();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const uploadProof = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedId) return;
    try {
      await api.issues.uploadPhoto(selectedId, await compressImage(file), "resolution");
      toast.success("Proof photo added to the public report");
      refreshDetail();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Upload failed");
    }
  };

  const toggleChecked = (id: string) =>
    setChecked((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  const issues = data?.data.items ?? [];
  const officers = officersData?.data.items ?? [];
  const selected = issues.find((i) => i.id === selectedId) ?? detailData?.data.issue;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Issue queue"
        title="Reports to work on"
        description="Most urgent first. Verify, assign, update or escalate, and leave private notes for your team."
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
            className={`shrink-0 label-caps border-2 px-3 py-1.5 text-xs transition-colors ${
              statusFilter === tab.value
                ? "border-primary bg-primary text-primary-foreground"
                : "border-foreground/30 bg-card text-muted-foreground hover:border-foreground/60 hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          aria-pressed={mineOnly}
          onClick={() => setMineOnly((v) => !v)}
          className={`label-caps border-2 px-3 py-1.5 text-xs ${
            mineOnly ? "border-primary bg-primary text-primary-foreground" : "border-foreground/30 text-muted-foreground"
          }`}
        >
          Assigned to me
        </button>
        <button
          type="button"
          aria-pressed={overdueOnly}
          onClick={() => setOverdueOnly((v) => !v)}
          className={`label-caps border-2 px-3 py-1.5 text-xs ${
            overdueOnly ? "border-destructive bg-destructive text-white" : "border-foreground/30 text-muted-foreground"
          }`}
        >
          Overdue
        </button>
        <select
          aria-label="Department"
          value={departmentFilter}
          onChange={(e) => setDepartmentFilter(e.target.value)}
          className="h-8 border-2 border-foreground/30 bg-card px-2 text-xs capitalize"
        >
          <option value="">All departments</option>
          {departments.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </div>

      {/* Phones: cards. The table below takes over from md up. */}
      <div className="space-y-3 md:hidden">
        {isLoading && (
          <Card className="py-8 text-center text-sm text-muted-foreground">Loading queue…</Card>
        )}
        {!isLoading && issues.length === 0 && (
          <Card className="py-8 text-center text-sm text-muted-foreground">
            No reports in this filter.
          </Card>
        )}
        {issues.map((issue) => (
          <button
            key={issue.id}
            type="button"
            onClick={() => {
              setSelectedId(issue.id);
              setTimeout(
                () => document.getElementById("triage-actions")?.scrollIntoView({ behavior: "smooth" }),
                150
              );
            }}
            className={`block w-full border bg-card p-4 text-left ${
              selectedId === issue.id ? "border-2 border-primary" : "border-card-border"
            }`}
          >
            <span className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-board text-xs text-muted-foreground">{issue.issue_number}</span>
              <StatusBadge status={issue.status} />
            </span>
            <span className="text-display mt-2 block text-lg leading-snug">
              {issue.is_emergency && (
                <AlertTriangle className="mr-1.5 inline h-4 w-4 text-destructive" />
              )}
              {issue.title ?? issue.description}
            </span>
            <span className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
              <span>{issue.location.station.name}</span>
              <span>{issue.category?.name ?? "General"}</span>
              <span>{issue.support_count} backing</span>
              <span>{formatRelativeTime(issue.created_at)}</span>
              <SlaChip issue={issue} now={now} />
            </span>
          </button>
        ))}
      </div>

      {checked.length > 0 && (
        <Card className="flex flex-col gap-2 border-2 border-primary p-3 md:flex-row md:items-center">
          <p className="label-caps shrink-0 text-xs">{checked.length} selected</p>
          <select
            aria-label="New status"
            value={bulkStatus}
            onChange={(e) => setBulkStatus(e.target.value)}
            className="h-11 border border-card-border bg-card px-2 text-xs md:h-9"
          >
            <option value="verified">Verified</option>
            <option value="action_started">Action started</option>
            <option value="completed">Completed</option>
            <option value="rejected">Rejected</option>
          </select>
          <input
            value={bulkRemarks}
            onChange={(e) => setBulkRemarks(e.target.value)}
            placeholder="Remark for the timeline (required)"
            className="h-11 min-w-0 flex-1 border border-card-border bg-card px-2 text-xs md:h-9"
          />
          <Button
            size="sm"
            variant="accent"
            disabled={bulkMutation.isPending || bulkRemarks.trim().length < 5}
            onClick={() => bulkMutation.mutate()}
          >
            Update all
          </Button>
        </Card>
      )}

      <Card className="hidden overflow-hidden p-0 md:block">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[660px] text-left text-sm">
            <thead>
              <tr className="border-b border-card-border bg-muted/40 text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                <th className="px-3 py-3.5">
                  <span className="sr-only">Select</span>
                </th>
                <th className="px-5 py-3.5">Backing</th>
                <th className="px-5 py-3.5">Grievance</th>
                <th className="px-5 py-3.5">Station</th>
                <th className="px-5 py-3.5">Category</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5">Target</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td colSpan={7} className="px-5 py-12 text-center text-muted-foreground">
                    Loading station triage queue…
                  </td>
                </tr>
              )}
              {!isLoading && issues.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-5 py-12 text-center text-muted-foreground">
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
                  <td className="px-3 py-4" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      aria-label={`Select ${issue.issue_number}`}
                      checked={checked.includes(issue.id)}
                      onChange={() => toggleChecked(issue.id)}
                    />
                  </td>
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
                    <SlaChip issue={issue} now={now} />
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
            id="triage-actions"
            className="scroll-mt-4"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
          >
            <Card elevated className="space-y-5 p-4 sm:p-6 border-accent/40 bg-card">
              <div className="flex flex-col items-start gap-3 sm:flex-row sm:justify-between">
                <div className="min-w-0">
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
                  className="inline-flex shrink-0 items-center gap-1 text-xs font-semibold text-accent hover:underline"
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
                      className="h-11 w-full rounded-xl border border-card-border bg-card px-3 text-xs md:h-9"
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
                      className="h-11 w-full rounded-xl border border-card-border bg-card px-3 text-xs md:h-9"
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
                      className="h-11 w-full rounded-xl border border-card-border bg-card px-3 text-xs md:h-9"
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

              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div className="space-y-2 border border-card-border bg-background p-4">
                  <Label htmlFor="department">Department</Label>
                  <select
                    id="department"
                    value={selected.department ?? ""}
                    onChange={(e) => departmentMutation.mutate(e.target.value)}
                    className="h-11 w-full border border-card-border bg-card px-3 text-xs capitalize md:h-9"
                  >
                    <option value="">Not set</option>
                    {departments.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                  {aiStatus?.data.enabled && (
                    <TriageSuggestion
                      issueId={selected.id}
                      onUseDepartment={(d) => departmentMutation.mutate(d)}
                    />
                  )}
                  <label className="label-caps mt-2 inline-flex cursor-pointer items-center gap-1.5 text-xs text-accent hover:underline">
                    <Camera className="h-3.5 w-3.5" /> Add proof-of-fix photo
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => void uploadProof(e)}
                    />
                  </label>
                  {aiStatus?.data.enabled &&
                    detailPhotos.some((p) => p.kind === "resolution") &&
                    detailPhotos.some((p) => (p.kind ?? "evidence") === "evidence") && (
                      <FixCheck issueId={selected.id} />
                    )}
                </div>

                <div className="space-y-2 border border-card-border bg-background p-4">
                  <Label htmlFor="merge">Merge duplicate into</Label>
                  <select
                    id="merge"
                    value={mergeTarget}
                    onChange={(e) => setMergeTarget(e.target.value)}
                    className="h-11 w-full border border-card-border bg-card px-3 text-xs md:h-9"
                  >
                    <option value="">Choose a report at this station</option>
                    {issues
                      .filter(
                        (i) =>
                          i.id !== selected.id &&
                          i.location.station.code === selected.location.station.code
                      )
                      .map((i) => (
                        <option key={i.id} value={i.id}>
                          {i.issue_number}: {(i.title ?? i.description).slice(0, 40)}
                        </option>
                      ))}
                  </select>
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full"
                    disabled={!mergeTarget || mergeMutation.isPending}
                    onClick={() => mergeMutation.mutate()}
                  >
                    Merge
                  </Button>
                </div>

                <div className="space-y-2 border border-card-border bg-background p-4">
                  <Label htmlFor="note">Private note (staff only)</Label>
                  {notes.length > 0 && (
                    <ul className="max-h-28 space-y-1 overflow-y-auto text-xs text-muted-foreground">
                      {notes.map((n) => (
                        <li key={n.id}>{n.remarks}</li>
                      ))}
                    </ul>
                  )}
                  <Textarea
                    id="note"
                    rows={2}
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    className="min-h-0 text-xs"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full"
                    disabled={note.trim().length < 2 || noteMutation.isPending}
                    onClick={() => noteMutation.mutate()}
                  >
                    Save note
                  </Button>
                </div>
              </div>

              {/* Action Remarks */}
              <div className="space-y-1.5 pt-1">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <Label htmlFor="remarks" className="mb-0">
                    Update for the public timeline * (required)
                  </Label>
                  {aiStatus?.data.enabled && (
                    <button
                      type="button"
                      disabled={suggesting}
                      onClick={() => void suggestWording()}
                      className="label-caps inline-flex items-center gap-1.5 text-xs text-accent hover:underline disabled:opacity-50"
                    >
                      <Sparkles className="h-3.5 w-3.5" />
                      {suggesting ? "Writing…" : "Suggest wording from my notes"}
                    </button>
                  )}
                </div>
                <div className="flex flex-wrap gap-1.5 pb-1">
                  {TEMPLATES.map((text) => (
                    <button
                      key={text}
                      type="button"
                      onClick={() => setRemarks(text)}
                      className="max-w-full truncate border border-card-border px-2 py-1 text-left text-[11px] text-muted-foreground hover:text-foreground"
                    >
                      {text}
                    </button>
                  ))}
                </div>
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
