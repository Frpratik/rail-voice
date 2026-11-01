"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bell,
  ClipboardList,
  Home,
  MapPin,
  Moon,
  Plus,
  Shield,
  Sun,
  User,
} from "lucide-react";
import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";
import { useAuthStore } from "@/lib/auth-store";
import { isOfficial } from "@/lib/roles";
import { cn } from "@/lib/utils";

const emptySubscribe = () => () => {};
const getClientSnapshot = () => true;
const getServerSnapshot = () => false;

/** Square rail-sign mark: two rails and sleepers on a yellow plate. */
function LogoMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "flex h-9 w-9 items-center justify-center rounded-sm border-2 border-[#101a33] bg-[#f5b800] text-[#101a33]",
        className
      )}
      aria-hidden
    >
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="square">
        <path d="M8 3 5 21M16 3l3 18" />
        <path d="M6.5 8h11M5.8 13h12.4M5.2 18h13.6" />
      </svg>
    </span>
  );
}

export function AppHeader() {
  const { resolvedTheme, setTheme } = useTheme();
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);
  const mounted = useSyncExternalStore(emptySubscribe, getClientSnapshot, getServerSnapshot);

  if (pathname.startsWith("/admin")) return null;

  const isLogin = pathname.startsWith("/login");
  const official = isOfficial(user?.roles);

  const navItems = [
    { href: "/", label: "Feed" },
    { href: "/stations", label: "Stations" },
    { href: "/my-issues", label: "My Issues" },
    { href: "/report", label: "Report" },
    ...(official ? [{ href: "/admin/dashboard", label: "Control Room" }] : []),
  ];

  const iconBtn =
    "flex h-10 w-10 items-center justify-center rounded-sm text-white/80 transition-colors hover:bg-white/10 hover:text-white";

  return (
    <header className="sticky top-0 z-40 bg-[#0d2252] text-white">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:h-16 sm:px-6">
        <Link href="/" className="flex items-center gap-3">
          <LogoMark />
          <span className="text-display text-xl uppercase tracking-[0.04em] sm:text-2xl">
            Rail<span className="text-[#f5b800]">Voice</span>
          </span>
        </Link>

        {!isLogin && (
          <nav className="hidden items-stretch self-stretch lg:flex">
            {navItems.map((item) => {
              const active =
                item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "label-caps relative flex items-center px-4 text-sm transition-colors",
                    active ? "text-[#f5b800]" : "text-white/75 hover:text-white"
                  )}
                >
                  {item.label}
                  {active && (
                    <span className="absolute inset-x-3 bottom-0 h-1 bg-[#f5b800]" />
                  )}
                </Link>
              );
            })}
          </nav>
        )}

        <div className="flex items-center gap-1">
          {mounted && (
            <button
              type="button"
              className={iconBtn}
              onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
              aria-label="Toggle theme"
            >
              {resolvedTheme === "dark" ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </button>
          )}
          {!isLogin && (
            <>
              {official && (
                <Link href="/admin/dashboard" className={cn(iconBtn, "hidden sm:flex")} aria-label="Control room">
                  <Shield className="h-4 w-4 text-[#f5b800]" />
                </Link>
              )}
              <Link href="/notifications" className={iconBtn} aria-label="Notifications">
                <Bell className="h-4 w-4" />
              </Link>
              <Link href="/profile" className={iconBtn} aria-label="Profile">
                <User className="h-4 w-4" />
              </Link>
              <Link
                href="/report"
                className="label-caps ml-2 hidden h-10 items-center rounded-sm border-2 border-[#101a33] bg-[#f5b800] px-4 text-sm text-[#101a33] transition-colors hover:bg-[#ffd24d] lg:inline-flex"
              >
                Report issue
              </Link>
            </>
          )}
        </div>
      </div>
      <div className="platform-edge" />
    </header>
  );
}

export function BottomNav() {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);

  if (pathname.startsWith("/admin") || pathname.startsWith("/login")) return null;

  const official = isOfficial(user?.roles);

  const items = [
    { href: "/", icon: Home, label: "Home" },
    { href: "/stations", icon: MapPin, label: "Stations" },
    { href: "/report", icon: Plus, label: "Report", accent: true },
    { href: "/my-issues", icon: ClipboardList, label: "My issues" },
    ...(official
      ? [{ href: "/admin/dashboard", icon: Shield, label: "Control" }]
      : [{ href: "/profile", icon: User, label: "Profile" }]),
  ];

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t-4 border-t-[#f5b800] bg-[#0d2252] pb-safe lg:hidden">
      <div className="mx-auto flex h-16 max-w-lg items-center justify-around px-2">
        {items.map(({ href, icon: Icon, label, accent }) => {
          const active = pathname === href;
          if (accent) {
            return (
              <Link key={href} href={href} className="-mt-7" aria-label="Report issue">
                <div className="flex h-14 w-14 items-center justify-center rounded-sm border-2 border-[#101a33] bg-[#f5b800] text-[#101a33]">
                  <Icon className="h-6 w-6" strokeWidth={2.6} />
                </div>
              </Link>
            );
          }
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "label-caps flex min-w-0 flex-1 flex-col items-center gap-1 px-1 py-1.5 text-center text-[10px] tracking-[0.06em] transition-colors",
                active ? "text-[#f5b800]" : "text-white/70"
              )}
            >
              <Icon className="h-5 w-5" />
              {label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

export function SiteFooter() {
  const pathname = usePathname();
  if (pathname.startsWith("/admin") || pathname.startsWith("/login")) return null;

  return (
    <footer className="mt-auto bg-[#0d2252] text-white">
      <div className="platform-edge" />
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 pb-28 pt-8 sm:px-6 md:flex-row md:items-end md:justify-between lg:pb-10 lg:pt-10">
        <div>
          <div className="mb-3 flex items-center gap-3">
            <LogoMark />
            <span className="text-display text-2xl uppercase tracking-[0.04em]">
              Rail<span className="text-[#f5b800]">Voice</span>
            </span>
          </div>
          <p className="max-w-sm text-sm leading-relaxed text-white/70">
            Report and track problems at stations on the Western Railway
            suburban line, Churchgate to Virar.
          </p>
        </div>
        <div className="label-caps flex flex-wrap gap-x-6 gap-y-3 text-sm text-white/70">
          <Link href="/" className="transition-colors hover:text-[#f5b800]">
            Feed
          </Link>
          <Link href="/stations" className="transition-colors hover:text-[#f5b800]">
            Stations
          </Link>
          <Link href="/my-issues" className="transition-colors hover:text-[#f5b800]">
            My Issues
          </Link>
          <Link href="/report" className="transition-colors hover:text-[#f5b800]">
            Report
          </Link>
          <Link href="/help" className="transition-colors hover:text-[#f5b800]">
            Help
          </Link>
          <Link href="/privacy" className="transition-colors hover:text-[#f5b800]">
            Privacy
          </Link>
          <Link href="/terms" className="transition-colors hover:text-[#f5b800]">
            Terms
          </Link>
        </div>
      </div>
    </footer>
  );
}

export { LogoMark };
