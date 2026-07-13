"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { Check, ChevronLeft } from "lucide-react";
import { DuplicateSheet } from "@/components/issues/duplicate-sheet";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input, Label, Select, Textarea } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/empty-state";
import { api, ApiError } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import type { SimilarIssue } from "@/lib/types";
import { cn } from "@/lib/utils";

const STEPS = ["Location", "Details", "Review"];

export default function ReportPage() {
  const router = useRouter();
  const { user, anonymousSessionId, setAnonymous } = useAuthStore();
  const [step, setStep] = useState(1);
  const [stationId, setStationId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [duplicateOpen, setDuplicateOpen] = useState(false);
  const [similarIssues, setSimilarIssues] = useState<SimilarIssue[]>([]);
  const [threshold, setThreshold] = useState(0.82);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [divergenceReason, setDivergenceReason] = useState("");
  const [checking, setChecking] = useState(false);
  const [photoFiles, setPhotoFiles] = useState<File[]>([]);

  const { data: stationsData } = useQuery({
    queryKey: ["stations"],
    queryFn: () => api.stations.list({ zone_code: "WR" }),
  });
  const stations = stationsData?.data ?? [];

  const ensureSession = async () => {
    if (user) return;
    const existing =
      anonymousSessionId ||
      (typeof window !== "undefined"
        ? localStorage.getItem("anonymous_session_id")
        : null);
    if (existing) {
      if (!anonymousSessionId) setAnonymous(existing);
      return;
    }
    const res = await api.auth.anonymous();
    setAnonymous(res.data.anonymous_session_id);
  };

  const submitCheck = async () => {
    if (description.length < 20) {
      toast.error("Description must be at least 20 characters");
      return;
    }
    if (!stationId) {
      toast.error("Please select a station");
      return;
    }
    setChecking(true);
    try {
      await ensureSession();
      const res = await api.issues.checkDuplicates({
        description,
        station_id: stationId,
        title: title || undefined,
      });
      if (res.data.has_similar) {
        setSimilarIssues(res.data.similar_issues);
        setThreshold(res.data.threshold);
        setDuplicateOpen(true);
      } else {
        await createIssue(false);
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Check failed");
    } finally {
      setChecking(false);
    }
  };

  const createIssue = async (force: boolean) => {
    await ensureSession();
    try {
      const res = await api.issues.create({
        description,
        station_id: stationId,
        title: title || undefined,
        force_create: force,
        divergence_reason: force ? divergenceReason : undefined,
      });
      const issueId = res.data.issue.id;
      for (const file of photoFiles.slice(0, 5)) {
        try {
          await api.issues.uploadPhoto(issueId, file);
        } catch {
          toast.error(`Could not upload ${file.name}`);
        }
      }
      toast.success("Issue submitted successfully");
      setDuplicateOpen(false);
      router.push(`/issues/${issueId}`);
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        const detail = e.details as { similar_issues?: SimilarIssue[] };
        setSimilarIssues(detail?.similar_issues ?? []);
        setDuplicateOpen(true);
        return;
      }
      toast.error(e instanceof Error ? e.message : "Submit failed");
    }
  };

  const supportMutation = useMutation({
    mutationFn: (id: string) => api.issues.support(id),
    onSuccess: (res) => {
      toast.success(res.data.message);
      setDuplicateOpen(false);
      router.push(`/issues/${res.data.issue_id}`);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="mx-auto max-w-xl">
      <PageHeader
        eyebrow="Report"
        title="Tell us what’s wrong"
        description="Three quick steps. AI checks for similar issues before you create a new one."
      />

      {/* Step indicator */}
      <div className="mb-8 flex items-center gap-2">
        {STEPS.map((label, i) => {
          const n = i + 1;
          const done = step > n;
          const current = step === n;
          return (
            <div key={label} className="flex flex-1 flex-col gap-2">
              <div
                className={cn(
                  "h-1.5 rounded-full transition-colors duration-300",
                  done || current ? "bg-accent" : "bg-muted"
                )}
              />
              <div className="flex items-center gap-1.5">
                <span
                  className={cn(
                    "flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold",
                    done || current
                      ? "bg-accent text-accent-foreground"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {done ? <Check className="h-3 w-3" /> : n}
                </span>
                <span
                  className={cn(
                    "text-[11px] font-medium",
                    current ? "text-foreground" : "text-muted-foreground"
                  )}
                >
                  {label}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.div
            key="s1"
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -12 }}
          >
            <Card elevated className="space-y-5 p-6">
              <div>
                <Label htmlFor="station">Station</Label>
                <Select
                  id="station"
                  value={stationId}
                  onChange={(e) => setStationId(e.target.value)}
                >
                  <option value="">Select a station</option>
                  {stations.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.code})
                    </option>
                  ))}
                </Select>
              </div>
              <Button
                variant="accent"
                className="w-full"
                size="lg"
                onClick={() => setStep(2)}
                disabled={!stationId}
              >
                Continue
              </Button>
            </Card>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div
            key="s2"
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -12 }}
          >
            <Card elevated className="space-y-5 p-6">
              <div>
                <Label htmlFor="description">What’s the problem?</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe what you see — location details help a lot…"
                />
                <p className="mt-2 text-xs text-muted-foreground">
                  {description.length}/5000 · minimum 20 characters
                </p>
              </div>
              <div>
                <Label htmlFor="title">Short title (optional)</Label>
                <Input
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Missing dustbin near Platform 2"
                />
              </div>
              <div>
                <Label htmlFor="photos">Photos (optional, max 5)</Label>
                <Input
                  id="photos"
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  multiple
                  onChange={(e) =>
                    setPhotoFiles(Array.from(e.target.files ?? []).slice(0, 5))
                  }
                />
                {photoFiles.length > 0 && (
                  <p className="mt-2 text-xs text-muted-foreground">
                    {photoFiles.length} file(s) selected
                  </p>
                )}
              </div>
              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep(1)}>
                  <ChevronLeft className="h-4 w-4" />
                  Back
                </Button>
                <Button
                  className="flex-1"
                  variant="accent"
                  onClick={() => setStep(3)}
                  disabled={description.trim().length < 20}
                >
                  Continue
                </Button>
              </div>
            </Card>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div
            key="s3"
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -12 }}
          >
            <Card elevated className="space-y-5 p-6">
              <p className="text-sm leading-relaxed text-muted-foreground">
                Review your report. We’ll run a semantic duplicate check before
                creating anything new.
              </p>
              <div className="rounded-2xl bg-muted/60 p-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  Station
                </p>
                <p className="mt-1 font-semibold tracking-tight">
                  {stations.find((s) => s.id === stationId)?.name}
                </p>
                {title && (
                  <>
                    <p className="mt-4 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                      Title
                    </p>
                    <p className="mt-1 font-medium">{title}</p>
                  </>
                )}
                <p className="mt-4 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  Description
                </p>
                <p className="mt-1 text-sm leading-relaxed text-foreground/90">
                  {description}
                </p>
              </div>
              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep(2)}>
                  <ChevronLeft className="h-4 w-4" />
                  Back
                </Button>
                <Button
                  variant="accent"
                  className="flex-1"
                  size="lg"
                  disabled={checking}
                  onClick={submitCheck}
                >
                  {checking ? "Checking for similar issues…" : "Submit report"}
                </Button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      <DuplicateSheet
        open={duplicateOpen}
        similarIssues={similarIssues}
        threshold={threshold}
        loading={supportMutation.isPending || checking}
        showCreateForm={showCreateForm}
        divergenceReason={divergenceReason}
        onDivergenceChange={setDivergenceReason}
        onSupport={(id) => supportMutation.mutate(id)}
        onCreateAnyway={() => setShowCreateForm(true)}
        onConfirmCreate={() => createIssue(true)}
        onClose={() => {
          setDuplicateOpen(false);
          setShowCreateForm(false);
        }}
      />
    </div>
  );
}
