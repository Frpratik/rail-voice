import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-sm px-2 py-0.5 font-display text-xs font-semibold uppercase tracking-[0.1em]",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground",
        accent: "bg-accent text-accent-foreground",
        success: "bg-success/15 text-success border border-success/40",
        warning: "bg-warning/15 text-warning border border-warning/40",
        destructive: "bg-destructive/15 text-destructive border border-destructive/40",
        muted: "bg-muted text-foreground/80",
        emergency: "bg-destructive text-white blink",
        outline: "border border-foreground/40 text-foreground/80",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export function Badge({
  className,
  variant,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

const STATUS_MAP: Record<
  string,
  { label: string; variant: "default" | "warning" | "success" | "muted" | "destructive" | "accent" }
> = {
  submitted: { label: "Submitted", variant: "default" },
  under_review: { label: "Under review", variant: "accent" },
  verified: { label: "Verified", variant: "default" },
  assigned: { label: "Assigned", variant: "accent" },
  work_in_progress: { label: "In progress", variant: "warning" },
  action_started: { label: "Action started", variant: "warning" },
  waiting_for_material: { label: "Waiting", variant: "warning" },
  completed: { label: "Completed", variant: "success" },
  verified_complete: { label: "Verified done", variant: "success" },
  closed: { label: "Closed", variant: "muted" },
  rejected: { label: "Rejected", variant: "destructive" },
  spam: { label: "Spam hold", variant: "destructive" },
};

export function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_MAP[status] ?? {
    label: status.replace(/_/g, " "),
    variant: "muted" as const,
  };
  return (
    <span className="inline-flex shrink-0 items-stretch overflow-hidden whitespace-nowrap rounded-sm border border-foreground/25 bg-card font-display text-xs font-semibold uppercase tracking-[0.1em]">
      <span
        className={cn(
          "w-1.5",
          cfg.variant === "success" && "bg-success",
          cfg.variant === "warning" && "bg-warning",
          cfg.variant === "destructive" && "bg-destructive",
          cfg.variant === "accent" && "bg-accent",
          cfg.variant === "default" && "bg-primary",
          cfg.variant === "muted" && "bg-muted-foreground"
        )}
      />
      <span className="px-2 py-0.5">{cfg.label}</span>
    </span>
  );
}
