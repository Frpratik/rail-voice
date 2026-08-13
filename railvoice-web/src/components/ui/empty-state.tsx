"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Inbox, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  actionLabel,
  actionHref,
  onAction,
  action,
  className,
}: {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
  action?: { label: string; onClick?: () => void; href?: string };
  className?: string;
}) {
  const finalLabel = action?.label ?? actionLabel;
  const finalHref = action?.href ?? actionHref;
  const finalOnClick = action?.onClick ?? onAction;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "flex flex-col items-center rounded-3xl border border-dashed border-card-border bg-card/50 px-6 py-14 text-center",
        className
      )}
    >
      <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
        <Icon className="h-6 w-6" strokeWidth={1.75} />
      </div>
      <h3 className="text-display text-lg font-semibold tracking-tight">{title}</h3>
      <p className="mt-2 max-w-sm text-sm leading-relaxed text-muted-foreground">
        {description}
      </p>
      {finalLabel && finalHref && (
        <Link href={finalHref} className="mt-6">
          <Button variant="accent">{finalLabel}</Button>
        </Link>
      )}
      {finalLabel && finalOnClick && !finalHref && (
        <Button variant="accent" className="mt-6" onClick={finalOnClick}>
          {finalLabel}
        </Button>
      )}
    </motion.div>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="max-w-2xl">
        {eyebrow && (
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-accent">
            {eyebrow}
          </p>
        )}
        <h1 className="text-display text-3xl font-semibold tracking-tight sm:text-4xl">
          {title}
        </h1>
        {description && (
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground sm:text-[15px]">
            {description}
          </p>
        )}
      </div>
      {action}
    </div>
  );
}
