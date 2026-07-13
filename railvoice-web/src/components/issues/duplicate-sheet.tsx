"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Sparkles, X } from "lucide-react";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label, Textarea } from "@/components/ui/input";
import type { SimilarIssue } from "@/lib/types";

export function DuplicateSheet({
  open,
  similarIssues,
  threshold,
  loading,
  showCreateForm,
  divergenceReason,
  onDivergenceChange,
  onSupport,
  onCreateAnyway,
  onConfirmCreate,
  onClose,
}: {
  open: boolean;
  similarIssues: SimilarIssue[];
  threshold: number;
  loading?: boolean;
  showCreateForm: boolean;
  divergenceReason: string;
  onDivergenceChange: (v: string) => void;
  onSupport: (id: string) => void;
  onCreateAnyway: () => void;
  onConfirmCreate: () => void;
  onClose: () => void;
}) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/45 backdrop-blur-md"
            onClick={onClose}
          />
          <motion.div
            initial={{ y: "100%", opacity: 0.8 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: "100%", opacity: 0 }}
            transition={{ type: "spring", damping: 30, stiffness: 320 }}
            className="fixed inset-x-0 bottom-0 z-50 max-h-[90vh] overflow-y-auto rounded-t-[28px] border border-card-border bg-card p-6 shadow-2xl md:inset-x-auto md:bottom-auto md:left-1/2 md:top-1/2 md:max-w-lg md:-translate-x-1/2 md:-translate-y-1/2 md:rounded-3xl"
            role="dialog"
            aria-labelledby="duplicate-title"
            aria-modal="true"
          >
            <div className="mx-auto mb-5 h-1 w-10 rounded-full bg-muted md:hidden" />

            <div className="mb-6 flex items-start justify-between gap-3">
              <div>
                <div className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-accent/10 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-accent">
                  <Sparkles className="h-3 w-3" />
                  AI Match
                </div>
                <h2
                  id="duplicate-title"
                  className="text-display text-2xl font-semibold tracking-tight"
                >
                  We found similar issues
                </h2>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  Supporting an existing report helps officials prioritize faster
                  than creating a duplicate.
                </p>
              </div>
              <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close">
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="space-y-3">
              {similarIssues.map((item, idx) => (
                <div
                  key={item.id}
                  className={`rounded-2xl border p-4 transition-colors ${
                    idx === 0
                      ? "border-accent/30 bg-accent/[0.04] shadow-[0_0_0_1px_var(--glow)]"
                      : "border-card-border bg-background/40"
                  }`}
                >
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <Badge variant="accent">
                      {Math.round(item.similarity * 100)}% match
                    </Badge>
                    <span className="font-mono text-[11px] text-muted-foreground">
                      {item.issue_number}
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold tracking-tight">
                    {item.title ?? item.description_preview}
                  </h3>
                  <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                    {item.description_preview}
                  </p>
                  <div className="mt-3 flex items-center justify-between">
                    <span className="text-sm font-medium">
                      {item.support_count} supports
                    </span>
                    <StatusBadge status={item.status} />
                  </div>
                  <Button
                    variant="accent"
                    className="mt-3 w-full"
                    disabled={loading}
                    onClick={() => onSupport(item.id)}
                    aria-label={`Support issue ${item.issue_number}, ${item.support_count} supporters`}
                  >
                    Support this issue
                  </Button>
                </div>
              ))}
            </div>

            <div className="my-6 flex items-center gap-3">
              <div className="h-px flex-1 bg-border" />
              <span className="text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
                or
              </span>
              <div className="h-px flex-1 bg-border" />
            </div>

            {!showCreateForm ? (
              <Button variant="outline" className="w-full" onClick={onCreateAnyway}>
                Create as new issue
              </Button>
            ) : (
              <div className="space-y-3">
                <div>
                  <Label htmlFor="divergence">
                    Why is this different? (min 10 characters)
                  </Label>
                  <Textarea
                    id="divergence"
                    value={divergenceReason}
                    onChange={(e) => onDivergenceChange(e.target.value)}
                    placeholder="e.g. Different end of the platform — north vs south"
                  />
                </div>
                <Button
                  className="w-full"
                  disabled={loading || divergenceReason.trim().length < 10}
                  onClick={onConfirmCreate}
                >
                  Confirm create
                </Button>
              </div>
            )}

            <p className="mt-5 text-center text-[11px] text-muted-foreground">
              Similarity threshold · {threshold}
            </p>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
