"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AdminSidebar } from "@/components/layout/admin-sidebar";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="fixed inset-0 z-50 flex bg-background">
      <AdminSidebar pathname={pathname} />
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex h-14 items-center justify-between border-b-2 border-foreground/70 bg-card px-5 lg:h-16 lg:px-8">
          <div className="flex items-center gap-3 lg:hidden">
            <Link href="/admin/dashboard" className="text-display text-lg uppercase">
              RailVoice Control
            </Link>
          </div>
          <nav className="flex gap-1 overflow-x-auto lg:hidden">
            {[
              { href: "/admin/dashboard", label: "Overview" },
              { href: "/admin/issues", label: "Issue Triage" },
              { href: "/admin/reports", label: "Reports" },
              { href: "/admin/users", label: "Users" },
            ].map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={`shrink-0 label-caps px-2.5 py-1.5 text-xs ${
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
            className="label-caps hidden text-sm text-muted-foreground transition-colors hover:text-foreground sm:inline"
          >
            ← Public site
          </Link>
        </header>
        <div className="flex-1 overflow-y-auto p-5 sm:p-8">{children}</div>
      </div>
    </div>
  );
}
