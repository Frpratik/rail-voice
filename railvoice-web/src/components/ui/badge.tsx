import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold tracking-wide uppercase",
  {
    variants: {
      variant: {
        default: "bg-primary/8 text-primary",
        accent: "bg-accent/12 text-accent",
        success: "bg-success/12 text-success",
        warning: "bg-warning/12 text-warning",
        destructive: "bg-destructive/12 text-destructive",
        muted: "bg-muted text-muted-foreground normal-case tracking-normal font-medium",
        emergency: "bg-destructive/15 text-destructive animate-pulse",
        outline: "border border-border text-muted-foreground normal-case tracking-normal font-medium",
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
