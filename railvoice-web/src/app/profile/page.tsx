"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { motion } from "framer-motion";
import { Award, Download, LogOut, Shield, Trash2, TrainFront, Type, UserCheck } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { isOfficial, personaLabel, resolvePersona } from "@/lib/roles";
import { applyTextSize, getTextSize, type TextSize } from "@/providers/app-settings";

export default function ProfilePage() {
  const { user, logout } = useAuthStore();
  const [textSize, setTextSize] = useState<TextSize>(() =>
    typeof window === "undefined" ? "normal" : getTextSize()
  );
  const { data: reputationData } = useQuery({
    queryKey: ["reputation"],
    queryFn: () => api.me.reputation(),
    enabled: !!user,
  });
  const reputation = reputationData?.data;

  const toggleTextSize = () => {
    const next = textSize === "large" ? "normal" : "large";
    setTextSize(next);
    applyTextSize(next);
  };

  const downloadData = async () => {
    try {
      const res = await api.me.exportData();
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(res.data, null, 2)], { type: "application/json" })
      );
      const a = document.createElement("a");
      a.href = url;
      a.download = "railvoice-my-data.json";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Couldn't download your data");
    }
  };

  const deleteAccount = async () => {
    const sure = window.confirm(
      "Delete your account? Your name and details are removed. Reports stay as a public record without your name. This can't be undone."
    );
    if (!sure) return;
    try {
      await api.me.deleteAccount();
      logout();
      toast.success("Your account has been deleted");
      window.location.href = "/";
    } catch {
      toast.error("Couldn't delete your account");
    }
  };

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

      <Card elevated className="space-y-5 p-4 sm:p-6">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10 text-accent">
            <UserCheck className="h-7 w-7" />
          </div>
          <div className="min-w-0">
            <h2 className="text-base font-semibold text-foreground">
              {user.display_name}
            </h2>
            <p className="text-xs font-semibold uppercase tracking-wider text-accent">
              {label}
            </p>
          </div>
        </div>

        <div className="rounded-xl border border-card-border bg-muted/30 p-4 space-y-2 text-xs">
          <div className="flex justify-between gap-4">
            <span className="text-muted-foreground">Account Status:</span>
            <span className="text-right font-semibold text-success">Verified Active</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-muted-foreground">Assigned Roles:</span>
            <span className="min-w-0 text-right font-semibold">{user.roles.join(", ") || "Passenger"}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-muted-foreground">Corridor Division:</span>
            <span className="text-right font-semibold">Western Railway (Mumbai)</span>
          </div>
        </div>

        {reputation && (
          <div className="space-y-3 border-2 border-card-border p-4">
            <div className="flex items-baseline justify-between gap-3">
              <p className="text-display text-xl">Your points</p>
              <p className="font-board text-2xl">{reputation.points}</p>
            </div>
            <p className="text-sm text-muted-foreground">
              {reputation.reports} reports · {reputation.backed} backed · {reputation.fixed} fixed
            </p>
            {reputation.badges.length > 0 && (
              <ul className="flex flex-wrap gap-2">
                {reputation.badges.map((badge) => (
                  <li
                    key={badge.code}
                    title={badge.description}
                    className="label-caps inline-flex items-center gap-1 bg-accent px-2 py-1 text-xs text-accent-foreground"
                  >
                    <Award className="h-3.5 w-3.5" />
                    {badge.name}
                  </li>
                ))}
              </ul>
            )}
            <Link href="/leaderboard" className="text-sm text-accent underline">
              See the leaderboard
            </Link>
          </div>
        )}

        <Button variant="outline" onClick={toggleTextSize} className="w-full gap-2">
          <Type className="h-4 w-4" />
          {textSize === "large" ? "Use normal text" : "Use larger text"}
        </Button>

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

        <div className="flex flex-wrap justify-between gap-3 border-t border-dashed border-card-border pt-4 text-xs">
          <button
            type="button"
            onClick={() => void downloadData()}
            className="inline-flex items-center gap-1.5 text-muted-foreground hover:text-foreground"
          >
            <Download className="h-3.5 w-3.5" /> Download my data
          </button>
          <button
            type="button"
            onClick={() => void deleteAccount()}
            className="inline-flex items-center gap-1.5 text-destructive"
          >
            <Trash2 className="h-3.5 w-3.5" /> Delete my account
          </button>
        </div>
      </Card>
    </motion.div>
  );
}
