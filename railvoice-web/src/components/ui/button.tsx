import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-sm border-2 border-transparent font-display text-sm font-semibold uppercase tracking-[0.1em] transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-45 select-none",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/85",
        accent:
          "border-[#101a33] bg-accent text-accent-foreground hover:bg-[#ffd24d]",
        outline:
          "border-foreground/70 bg-transparent text-foreground hover:bg-foreground hover:text-background",
        ghost: "text-muted-foreground hover:bg-muted hover:text-foreground",
        secondary: "bg-muted text-foreground hover:bg-muted/70",
        destructive: "bg-destructive text-white hover:bg-destructive/90",
        soft: "bg-accent/20 text-foreground hover:bg-accent/35",
      },
      size: {
        default: "h-11 px-5",
        sm: "h-9 px-3.5 text-xs",
        lg: "h-12 px-7 text-[15px]",
        xl: "h-14 px-8 text-base",
        icon: "h-10 w-10",
        "icon-sm": "h-8 w-8",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
);
Button.displayName = "Button";

export { buttonVariants };
