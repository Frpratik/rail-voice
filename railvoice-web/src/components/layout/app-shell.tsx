"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  Bell,
  Home,
  MapPin,
  Moon,
  Plus,
  Sun,
  User,
} from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { EmergencyBanner } from "@/components/layout/emergency-banner";

function LogoMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "relative flex h-8 w-8 items-center justify-center rounded-xl bg-accent text-accent-foreground shadow-[0_4px_14px_var(--glow)]",
        className
      )}
      aria-hidden
    >
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.2">
        <path d="M4 17h16" strokeLinecap="round" />
        <path d="M6 17V9a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8" strokeLinecap="round" />
        <circle cx="8.5" cy="17" r="1.5" fill="currentColor" stroke="none" />
        <circle cx="15.5" cy="17" r="1.5" fill="currentColor" stroke="none" />
        <path d="M9 11h6" strokeLinecap="round" />
      </svg>
    </span>
  );
}

export function AppHeader() {
  const { resolvedTheme, setTheme } = useTheme();
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => setMounted(true), []);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  if (pathname.startsWith("/admin")) return null;

  const isLogin = pathname.startsWith("/login");

  return (
    <>
      <EmergencyBanner />
      <header
        className={cn(
          "sticky top-0 z-40 transition-all duration-300",
          scrolled
            ? "border-b border-card-border bg-card/80 shadow-[0_8px_30px_rgba(10,11,13,0.04)] backdrop-blur-2xl"
            : "border-b border-transparent bg-transparent"
        )}
      >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="group flex items-center gap-2.5">
          <LogoMark className="transition-transform duration-300 group-hover:scale-105" />
          <span className="text-display text-[17px] font-semibold tracking-tight">
            RailVoice
          </span>
        </Link>

        {!isLogin && (
          <nav className="hidden items-center gap-1 md:flex">
            {[
              { href: "/", label: "Feed" },
              { href: "/nearby", label: "Corridor" },
              { href: "/leaderboard", label: "Leaderboard" },
              { href: "/report", label: "Report" },
            ].map((item) => {
              const active =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "relative rounded-xl px-3.5 py-2 text-sm font-medium tracking-tight transition-colors",
                    active
                      ? "text-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {active && (
                    <motion.span
                      layoutId="nav-pill"
                      className="absolute inset-0 rounded-xl bg-muted"
                      transition={{ type: "spring", bounce: 0.2, duration: 0.4 }}
                    />
                  )}
                  <span className="relative z-10">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        )}

        <div className="flex items-center gap-1">
          {mounted && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
              aria-label="Toggle theme"
            >
              {resolvedTheme === "dark" ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </Button>
          )}
          {!isLogin && (
            <>
              <Link href="/notifications" className="hidden sm:block">
                <Button variant="ghost" size="icon" aria-label="Notifications">
                  <Bell className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/profile">
                <Button variant="ghost" size="icon" aria-label="Profile">
                  <User className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/report" className="ml-1 hidden md:block">
                <Button variant="accent" size="sm">
                  Report issue
                </Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
    </>
  );
}

export function BottomNav() {
  const pathname = usePathname();

  if (pathname.startsWith("/admin") || pathname.startsWith("/login")) return null;

  const items = [
    { href: "/", icon: Home, label: "Home" },
    { href: "/nearby", icon: MapPin, label: "Nearby" },
    { href: "/report", icon: Plus, label: "Report", accent: true },
    { href: "/notifications", icon: Bell, label: "Alerts" },
    { href: "/profile", icon: User, label: "Profile" },
  ];

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-card-border bg-card/90 pb-safe backdrop-blur-2xl md:hidden">
      <div className="mx-auto flex h-[68px] max-w-lg items-center justify-around px-2">
        {items.map(({ href, icon: Icon, label, accent }) => {
          const active = pathname === href;
          if (accent) {
            return (
              <Link key={href} href={href} className="-mt-8" aria-label="Report issue">
                <motion.div
                  whileTap={{ scale: 0.94 }}
                  className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent text-accent-foreground shadow-[0_10px_30px_var(--glow)]"
                >
                  <Icon className="h-6 w-6" strokeWidth={2.4} />
                </motion.div>
              </Link>
            );
          }
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex min-w-[52px] flex-col items-center gap-1 rounded-xl px-2 py-1.5 text-[10px] font-medium tracking-wide transition-colors",
                active ? "text-accent" : "text-muted-foreground"
              )}
            >
              <Icon className={cn("h-5 w-5", active && "stroke-[2.4]")} />
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
    <footer className="mt-auto hidden border-t border-card-border bg-card/40 py-10 md:block">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="mb-3 flex items-center gap-2.5">
            <LogoMark />
            <span className="text-display text-lg font-semibold tracking-tight">
              RailVoice
            </span>
          </div>
          <p className="max-w-sm text-sm leading-relaxed text-muted-foreground">
            Community-powered issue reporting for the Western Railway corridor.
            Churchgate → Virar.
          </p>
        </div>
        <div className="flex flex-wrap gap-6 text-sm text-muted-foreground">
          <Link href="/nearby" className="transition-colors hover:text-foreground">
            Stations
          </Link>
          <Link href="/report" className="transition-colors hover:text-foreground">
            Report
          </Link>
          <Link href="/login" className="transition-colors hover:text-foreground">
            Sign in
          </Link>
        </div>
      </div>
    </footer>
  );
}

export { LogoMark };
