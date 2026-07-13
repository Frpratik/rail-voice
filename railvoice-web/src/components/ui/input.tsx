import * as React from "react";
import { cn } from "@/lib/utils";

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "flex h-12 w-full rounded-xl border border-border bg-card px-4 text-sm tracking-tight text-foreground shadow-[inset_0_1px_2px_rgba(10,11,13,0.03)] transition-all placeholder:text-muted-foreground/70 hover:border-foreground/15 focus-visible:border-accent/40 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-accent/15 disabled:cursor-not-allowed disabled:opacity-50",
      className
    )}
    {...props}
  />
));
Input.displayName = "Input";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "flex min-h-[140px] w-full resize-y rounded-xl border border-border bg-card px-4 py-3.5 text-sm leading-relaxed tracking-tight text-foreground shadow-[inset_0_1px_2px_rgba(10,11,13,0.03)] transition-all placeholder:text-muted-foreground/70 hover:border-foreground/15 focus-visible:border-accent/40 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-accent/15 disabled:cursor-not-allowed disabled:opacity-50",
      className
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";

export function Label({
  className,
  ...props
}: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn(
        "mb-2 block text-[13px] font-medium tracking-tight text-foreground/80",
        className
      )}
      {...props}
    />
  );
}

export function Select({
  className,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "flex h-12 w-full appearance-none rounded-xl border border-border bg-card bg-[length:16px] bg-[right_14px_center] bg-no-repeat px-4 pr-10 text-sm tracking-tight text-foreground shadow-[inset_0_1px_2px_rgba(10,11,13,0.03)] transition-all hover:border-foreground/15 focus-visible:border-accent/40 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-accent/15 disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%235c6370' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")`,
      }}
      {...props}
    >
      {children}
    </select>
  );
}
