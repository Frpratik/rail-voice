import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold tracking-wide uppercase contrast-more:border contrast-more:border-current",
  {
    variants: {
      variant: {
        default: "bg-primary/10 text-primary dark:text-primary-foreground font-semibold",
        accent: "bg-accent/15 text-accent-foreground dark:text-accent font-semibold",
        success: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 font-semibold",
        warning: "bg-amber-500/15 text-amber-800 dark:text-amber-300 font-semibold",
        destructive: "bg-rose-500/15 text-rose-700 dark:text-rose-300 font-semibold",
        muted: "bg-muted text-foreground/80 normal-case tracking-normal font-medium",
        emergency: "bg-rose-500/20 text-rose-700 dark:text-rose-300 animate-pulse font-bold",
        outline: "border border-border text-foreground/80 normal-case tracking-normal font-medium",
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
    <Badge variant={cfg.variant} className="gap-1.5 normal-case tracking-normal">
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          cfg.variant === "success" && "bg-success",
          cfg.variant === "warning" && "bg-warning",
          cfg.variant === "destructive" && "bg-destructive",
          cfg.variant === "accent" && "bg-accent",
          cfg.variant === "default" && "bg-primary",
          cfg.variant === "muted" && "bg-muted-foreground"
        )}
      />
      {cfg.label}
    </Badge>
  );
}
