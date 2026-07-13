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
        <header className="flex h-14 items-center justify-between border-b border-card-border bg-card/40 px-5 backdrop-blur lg:h-16 lg:px-8">
          <div className="flex items-center gap-3 lg:hidden">
            <Link href="/admin/dashboard" className="text-sm font-semibold">
              RailVoice Ops
            </Link>
          </div>
          <nav className="flex gap-1 overflow-x-auto lg:hidden">
            {[
              { href: "/admin/dashboard", label: "Overview" },
              { href: "/admin/issues", label: "Queue" },
              { href: "/admin/analytics", label: "Analytics" },
              { href: "/admin/reports", label: "Reports" },
            ].map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={`shrink-0 rounded-lg px-2.5 py-1.5 text-xs font-medium ${
                  pathname.startsWith(l.href)
                    ? "bg-muted text-foreground"
                    : "text-muted-foreground"
                }`}
              >
                {l.label}
              </Link>
            ))}
          </nav>
          <Link
            href="/"
            className="hidden text-sm font-medium text-muted-foreground transition-colors hover:text-foreground sm:inline"
          >
            ← App
          </Link>
        </header>
        <div className="flex-1 overflow-y-auto p-5 sm:p-8">{children}</div>
      </div>
    </div>
  );
}
