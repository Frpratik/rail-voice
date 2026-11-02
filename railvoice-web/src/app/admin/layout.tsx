"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AdminSidebar } from "@/components/layout/admin-sidebar";
import { useAuthStore } from "@/lib/auth-store";
import { resolvePersona } from "@/lib/roles";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);
  const isMainAdmin = (user?.persona ?? resolvePersona(user?.roles)) === "main_admin";

  return (
    <div className="fixed inset-0 z-50 flex bg-background">
      <AdminSidebar pathname={pathname} />
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="shrink-0 border-b-2 border-foreground/70 bg-card lg:flex lg:h-16 lg:items-center lg:justify-end lg:px-8">
          <div className="flex h-12 items-center justify-between px-4 lg:hidden">
            <Link href="/admin/dashboard" className="text-display text-lg uppercase">
              RailVoice Control
            </Link>
            <Link href="/" className="label-caps text-xs text-muted-foreground">
              ← Public site
            </Link>
          </div>
          <nav className="flex gap-1 overflow-x-auto px-3 pb-2 lg:hidden">
            {[
              { href: "/admin/dashboard", label: "Overview" },
              { href: "/admin/issues", label: "Queue" },
              { href: "/admin/flags", label: "Flagged" },
              { href: "/admin/analytics", label: "Analytics" },
              { href: "/admin/handover", label: "Handover" },
              { href: "/admin/reports", label: "Reports" },
              { href: "/admin/users", label: "Users" },
              ...(isMainAdmin ? [{ href: "/admin/audit", label: "Audit" }] : []),
            ].map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={`label-caps shrink-0 px-2 py-1.5 text-xs ${
                  pathname.startsWith(l.href)
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground"
                }`}
              >
                {l.label}
              </Link>
            ))}
          </nav>
          <Link
            href="/"
            className="label-caps hidden text-sm text-muted-foreground transition-colors hover:text-foreground lg:inline"
          >
            ← Public site
          </Link>
        </header>
        <div className="min-w-0 flex-1 overflow-y-auto p-4 sm:p-8">{children}</div>
      </div>
    </div>
  );
}
