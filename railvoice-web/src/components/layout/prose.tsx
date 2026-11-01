import type { ReactNode } from "react";

export function Prose({ children }: { children: ReactNode }) {
  return (
    <div className="space-y-4 text-[15px] leading-relaxed text-foreground/90 [&_h2]:text-display [&_h2]:mt-8 [&_h2]:text-2xl [&_li]:ml-5 [&_li]:list-disc [&_ul]:space-y-1.5 [&_a]:text-accent [&_a]:underline">
      {children}
    </div>
  );
}
