"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { LogOut, Shield, TrainFront } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input, Label } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { isOpsPersona, personaLabel, resolvePersona } from "@/lib/roles";

export default function ProfilePage() {
  const { user, setAuth, logout, accessToken } = useAuthStore();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [profile, setProfile] = useState<{
    avatar_url?: string | null;
    mobile_last4?: string | null;
    created_at?: string | null;
    last_login_at?: string | null;
    status?: string;
    has_password?: boolean;
  } | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!user) return;
    setName(user.display_name);
    void api.me
      .get()
      .then((res) => {
        setProfile(res.data);
        setEmail(res.data.email || "");
        setName(res.data.display_name);
      })
      .catch(() => undefined);
  }, [user]);

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
          description="Sign in as Passenger, Station Admin, or Main Admin."
        />
        <Card elevated className="p-8 text-center">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10 text-accent">
            <TrainFront className="h-7 w-7" />
          </div>
          <p className="text-sm leading-relaxed text-muted-foreground">
            You can still report anonymously — signing in unlocks history and
            ops access for admins.
          </p>
          <Link href="/login" className="mt-6 block">
            <Button variant="accent" size="lg" className="w-full">
              Sign in
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

  const persona = user.persona ?? resolvePersona(user.roles);
  const label = user.persona_label ?? personaLabel(persona);
  const canOpenOps = isOpsPersona(persona);

  const saveProfile = async () => {
    setSaving(true);
    try {
      const res = await api.me.update({
        display_name: name,
        email: email || undefined,
      });
      if (accessToken) setAuth(res.data, accessToken);
      toast.success("Profile updated");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Update failed");
    } finally {
      setSaving(false);
    }
  };

  const changePassword = async () => {
    setSaving(true);
    try {
      await api.me.changePassword({
        current_password: currentPassword || undefined,
        new_password: newPassword,
      });
      toast.success("Password updated");
      setCurrentPassword("");
      setNewPassword("");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Password change failed");
    } finally {
      setSaving(false);
    }
  };

  const onAvatar = async (file: File | null) => {
    if (!file) return;
    try {
      const res = await api.me.uploadAvatar(file);
      setProfile((p) => ({ ...(p || {}), avatar_url: res.data.avatar_url }));
      toast.success("Avatar uploaded");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Upload failed");
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto max-w-md space-y-4"
    >
      <PageHeader eyebrow="Account" title={user.display_name} />

      <Card elevated className="space-y-4 p-6">
        <div className="flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center overflow-hidden rounded-2xl bg-muted">
            {profile?.avatar_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={profile.avatar_url} alt="" className="h-full w-full object-cover" />
            ) : (
              <TrainFront className="h-7 w-7 text-muted-foreground" />
            )}
          </div>
          <div>
            <span className="rounded-full bg-accent/10 px-3 py-1 text-xs font-semibold text-accent">
              {label}
            </span>
            <p className="mt-2 text-xs text-muted-foreground">
              {profile?.mobile_last4 ? `Mobile ·••••${profile.mobile_last4}` : "Verified account"}
            </p>
            <label className="mt-2 inline-block cursor-pointer text-xs font-medium text-accent hover:underline">
              Upload photo
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={(e) => void onAvatar(e.target.files?.[0] || null)}
              />
            </label>
          </div>
        </div>

        <div>
          <Label htmlFor="name">Display name</Label>
          <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div>
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <Button variant="accent" disabled={saving} onClick={() => void saveProfile()}>
          Save profile
        </Button>
      </Card>

      <Card elevated className="space-y-3 p-6">
        <p className="text-sm font-semibold tracking-tight">Change password</p>
        <p className="text-xs text-muted-foreground">
          Optional account password (OTP login still works). Use this if an admin reset your password.
        </p>
        {profile?.has_password && (
          <div>
            <Label htmlFor="cur">Current password</Label>
            <Input
              id="cur"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
            />
          </div>
        )}
        <div>
          <Label htmlFor="npw">New password</Label>
          <Input
            id="npw"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
        </div>
        <Button
          variant="outline"
          disabled={saving || newPassword.length < 8}
          onClick={() => void changePassword()}
        >
          Update password
        </Button>
      </Card>

      {canOpenOps && (
        <Link href="/admin/dashboard">
          <Card className="flex items-center gap-4 p-5 transition-all hover:border-accent/30 hover:shadow-md">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <Shield className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <p className="font-semibold tracking-tight">
                {persona === "main_admin" ? "Corridor console" : "Station console"}
              </p>
              <p className="text-sm text-muted-foreground">Dashboard, users & reports</p>
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
