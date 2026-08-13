"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { LogOut, Shield, TrainFront, UserCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { isOfficial, personaLabel, resolvePersona } from "@/lib/roles";

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
      <div className="mx-auto max-w-md space-y-6">
        <PageHeader
          eyebrow="Account"
          title="Citizen & Admin Profile"
          description="Sign in as Passenger, Station Admin, or Western Railway Authority."
        />
        <Card elevated className="p-8 text-center space-y-4">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10 text-accent">
            <TrainFront className="h-7 w-7" />
          </div>
          <p className="text-sm leading-relaxed text-muted-foreground">
            Sign in to track your reported problems, receive official station updates, or access the Station Admin console.
          </p>
          <Link href="/login" className="block pt-2">
            <Button variant="accent" size="lg" className="w-full">
              Sign In to RailVoice
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  const persona = user.persona ?? resolvePersona(user.roles);
  const label = user.persona_label ?? personaLabel(persona);
  const official = isOfficial(user.roles);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto max-w-md space-y-6"
    >
      <PageHeader eyebrow="Account" title={user.display_name} />

      <Card elevated className="space-y-5 p-6">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10 text-accent">
            <UserCheck className="h-7 w-7" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-foreground">
              {user.display_name}
            </h2>
            <p className="text-xs font-semibold uppercase tracking-wider text-accent">
              {label}
            </p>
          </div>
        </div>

        <div className="rounded-xl border border-card-border bg-muted/30 p-4 space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Account Status:</span>
            <span className="font-semibold text-success">Verified Active</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Assigned Roles:</span>
            <span className="font-semibold">{user.roles.join(", ") || "Passenger"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Corridor Division:</span>
            <span className="font-semibold">Western Railway (Mumbai)</span>
          </div>
        </div>

        {official && (
          <Link href="/admin/dashboard" className="block">
            <Button variant="accent" className="w-full gap-2">
              <Shield className="h-4 w-4" />
              Open Station Admin Operations
            </Button>
          </Link>
        )}

        <Button
          variant="outline"
          onClick={handleLogout}
          className="w-full gap-2 text-destructive border-destructive/20 hover:bg-destructive/10"
        >
          <LogOut className="h-4 w-4" />
          Sign Out
        </Button>
      </Card>
    </motion.div>
  );
}
