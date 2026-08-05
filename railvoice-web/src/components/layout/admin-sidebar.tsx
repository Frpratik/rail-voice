"use client";

import Link from "next/link";
import {
  BarChart3,
  FileText,
  Inbox,
  LayoutDashboard,
  LogOut,
  Search,
  Users,
  Briefcase,
  Map,
  Zap,
} from "lucide-react";
import { LogoMark } from "@/components/layout/app-shell";
import { useAuthStore } from "@/lib/auth-store";
import { personaLabel, resolvePersona } from "@/lib/roles";
import { cn } from "@/lib/utils";

const links = [
  { href: "/admin/dashboard", icon: LayoutDashboard, label: "Overview" },
  { href: "/admin/issues", icon: Inbox, label: "Queue" },
  { href: "/admin/users", icon: Users, label: "Users" },
  { href: "/admin/dispatch", icon: Zap, label: "AI Dispatch" },
  { href: "/admin/analytics", icon: BarChart3, label: "Analytics" },
  { href: "/admin/analytics/heatmap", icon: Map, label: "Corridor Heatmap" },
  { href: "/admin/reports", icon: FileText, label: "Reports" },
  { href: "/admin/vendors", icon: Briefcase, label: "Vendors" },
];

export function AdminSidebar({ pathname }: { pathname: string }) {
  const user = useAuthStore((s) => s.user);
  const persona = user?.persona ?? resolvePersona(user?.roles);
  const label = user?.persona_label ?? personaLabel(persona);

  return (
    <aside className="hidden w-[260px] shrink-0 border-r border-card-border bg-card/50 p-5 lg:flex lg:flex-col">
      <Link href="/" className="mb-6 flex items-center gap-2.5">
        <LogoMark />
        <div>
          <p className="text-sm font-semibold tracking-tight">RailVoice</p>
          <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
            {label}
          </p>
        </div>
      </Link>

      <button
        onClick={() => {
          const event = new KeyboardEvent("keydown", {
            key: "k",
            ctrlKey: true,
            bubbles: true,
          });
          window.dispatchEvent(event);
        }}
        className="mb-6 flex items-center justify-between gap-2 rounded-xl border border-border bg-muted/40 px-3 py-2 text-xs font-medium text-muted-foreground transition-all hover:border-foreground/20 hover:text-foreground"
      >
        <span className="flex items-center gap-2">
          <Search className="h-3.5 w-3.5" />
          <span>Quick Command...</span>
        </span>
        <kbd className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono font-semibold border border-border">
          ⌘K
        </kbd>
      </button>

      <nav className="flex flex-1 flex-col gap-1">
        {links.map(({ href, icon: Icon, label: linkLabel }) => {
          const active =
            href === "/admin/analytics"
              ? pathname === "/admin/analytics"
              : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium tracking-tight transition-all",
                active
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {linkLabel}
            </Link>
          );
        })}
      </nav>

      <Link
        href="/"
        className="mt-4 flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      >
        <LogOut className="h-4 w-4" />
        Exit to app
      </Link>
    </aside>
  );
}
