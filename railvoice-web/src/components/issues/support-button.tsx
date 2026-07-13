"use client";

import { motion } from "framer-motion";
import { ThumbsUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function SupportButton({
  supportCount,
  supported,
  loading,
  onSupport,
  className,
}: {
  supportCount: number;
  supported?: boolean;
  loading?: boolean;
  onSupport: () => void;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-stretch gap-4", className)}>
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Community support
          </p>
          <p className="mt-1 text-display text-3xl font-semibold tracking-tight">
            <motion.span
              key={supportCount}
              initial={{ y: 8, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              className="inline-block"
            >
              {supportCount}
            </motion.span>
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            voices amplifying this issue
          </p>
        </div>
      </div>
      <Button
        variant={supported ? "outline" : "accent"}
        size="lg"
        className="w-full"
        disabled={loading || supported}
        onClick={onSupport}
      >
        <ThumbsUp className="h-4 w-4" />
        {supported ? "You’re supporting this" : "Support this issue"}
      </Button>
    </div>
  );
}
