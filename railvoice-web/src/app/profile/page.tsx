"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { LogOut, Shield, TrainFront } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

const OFFICIAL_ROLES = [
  "station_moderator",
  "station_manager",
  "divisional_officer",
  "railway_admin",
  "super_admin",
];

export default function ProfilePage() {
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    try {
      if (user) await api.auth.logout();
    } catch {
      /* ignore */
    }
    logout();
  };

  if (!user) {
    return (
      <div className="mx-auto max-w-md">
        <PageHeader
          eyebrow="Account"
          title="Your profile"
          description="Sign in to track reports and receive updates."
        />
        <Card elevated className="p-8 text-center">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10 text-accent">
            <TrainFront className="h-7 w-7" />
          </div>
          <p className="text-sm leading-relaxed text-muted-foreground">
            You can still report anonymously — signing in unlocks history and
            push notifications.
          </p>
          <Link href="/login" className="mt-6 block">
            <Button variant="accent" size="lg" className="w-full">
              Sign in with OTP
            </Button>
          </Link>
          <Link href="/report" className="mt-3 block">
            <Button variant="outline" className="w-full">
              Continue anonymously
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  const isOfficial = user.roles.some((r) => OFFICIAL_ROLES.includes(r));

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto max-w-md space-y-4"
    >
      <PageHeader eyebrow="Account" title={user.display_name} />

      <Card elevated className="p-6">
        <p className="text-sm text-muted-foreground">
          {user.is_verified ? "Verified mobile account" : "Unverified"}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {user.roles.map((r) => (
            <span
              key={r}
              className="rounded-full bg-muted px-3 py-1 text-xs font-medium capitalize text-foreground/80"
            >
              {r.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      </Card>

      {isOfficial && (
        <Link href="/admin/dashboard">
          <Card className="flex items-center gap-4 p-5 transition-all hover:border-accent/30 hover:shadow-md">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <Shield className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <p className="font-semibold tracking-tight">Operations console</p>
              <p className="text-sm text-muted-foreground">
                Dashboard, queue & analytics
              </p>
            </div>
          </Card>
        </Link>
      )}

      <Button variant="outline" className="w-full" size="lg" onClick={handleLogout}>
        <LogOut className="h-4 w-4" />
        Log out
      </Button>
    </motion.div>
  );
}
