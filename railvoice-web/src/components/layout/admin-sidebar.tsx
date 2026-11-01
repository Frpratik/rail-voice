"use client";

import Link from "next/link";
import {
  FileText,
  Flag,
  Inbox,
  LayoutDashboard,
  LogOut,
  Users,
} from "lucide-react";
import { LogoMark } from "@/components/layout/app-shell";
import { useAuthStore } from "@/lib/auth-store";
import { personaLabel, resolvePersona } from "@/lib/roles";
import { cn } from "@/lib/utils";

const links = [
  { href: "/admin/dashboard", icon: LayoutDashboard, label: "Overview" },
  { href: "/admin/issues", icon: Inbox, label: "Issue queue" },
  { href: "/admin/flags", icon: Flag, label: "Flagged" },
  { href: "/admin/reports", icon: FileText, label: "Reports" },
  { href: "/admin/users", icon: Users, label: "Users" },
];

export function AdminSidebar({ pathname }: { pathname: string }) {
  const user = useAuthStore((s) => s.user);
  const persona = user?.persona ?? resolvePersona(user?.roles);
  const label = user?.persona_label ?? personaLabel(persona);

  return (
    <aside className="hidden w-[250px] shrink-0 flex-col bg-[#0d2252] text-white lg:flex">
      <Link href="/" className="flex items-center gap-3 p-5">
        <LogoMark />
        <div>
          <p className="text-display text-xl uppercase tracking-[0.04em]">
            Rail<span className="text-[#f5b800]">Voice</span>
          </p>
          <p className="label-caps text-[11px] text-white/60">{label}</p>
        </div>
      </Link>
      <div className="platform-edge" />

      <p className="label-caps px-5 pb-2 pt-6 text-[11px] text-white/50">Control room</p>
      <nav className="flex flex-1 flex-col">
        {links.map(({ href, icon: Icon, label: linkLabel }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "label-caps flex items-center gap-3 border-l-4 px-5 py-3 text-sm transition-colors",
                active
                  ? "border-[#f5b800] bg-white/10 text-[#f5b800]"
                  : "border-transparent text-white/75 hover:bg-white/5 hover:text-white"
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
        className="label-caps flex items-center gap-3 border-t border-white/15 px-5 py-4 text-sm text-white/70 transition-colors hover:text-white"
      >
        <LogOut className="h-4 w-4" />
        Public site
      </Link>
    </aside>
  );
}
