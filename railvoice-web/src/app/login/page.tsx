"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { LogoMark } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input, Label } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [mobile, setMobile] = useState("+91");
  const [otp, setOtp] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [mockOtp, setMockOtp] = useState<string | null>(null);

  const requestOtp = async () => {
    setLoading(true);
    try {
      const res = await api.auth.requestOtp(mobile);
      setSent(true);
      if (res.data.mock_otp) setMockOtp(res.data.mock_otp);
      toast.success("OTP sent");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async () => {
    setLoading(true);
    try {
      const res = await api.auth.verifyOtp(mobile, otp);
      setAuth(res.data.user, res.data.access_token, res.data.refresh_token);
      toast.success("Welcome to RailVoice");
      router.push("/");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Invalid OTP");
    } finally {
      setLoading(false);
    }
  };

  const continueWithGoogle = async () => {
    setLoading(true);
    try {
      const res = await api.auth.google({
        id_token: "mock-token",
        email: "dev.user@railvoice.local",
        name: "Dev Google User",
        google_id: "mock-google-dev",
      });
      setAuth(res.data.user, res.data.access_token, res.data.refresh_token);
      toast.success("Signed in with Google");
      router.push("/");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Google sign-in failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative mx-auto flex min-h-[70vh] max-w-md items-center">
      <div className="pointer-events-none absolute left-1/2 top-0 h-48 w-48 -translate-x-1/2 rounded-full bg-accent/20 blur-3xl" />
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative w-full"
      >
        <Card elevated className="space-y-6 p-8">
          <div className="text-center">
            <div className="mb-5 flex justify-center">
              <LogoMark className="!h-12 !w-12 !rounded-2xl" />
            </div>
            <h1 className="text-display text-2xl font-semibold tracking-tight">
              Sign in
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Track your issues and get resolution updates
            </p>
          </div>

          <div>
            <Label htmlFor="mobile">Mobile number</Label>
            <Input
              id="mobile"
              value={mobile}
              onChange={(e) => setMobile(e.target.value)}
              placeholder="+919876543210"
              inputMode="tel"
              autoComplete="tel"
            />
          </div>

          {!sent ? (
            <Button
              className="w-full"
              variant="accent"
              size="lg"
              disabled={loading || mobile.length < 13}
              onClick={requestOtp}
            >
              Send OTP
            </Button>
          ) : (
            <>
              {mockOtp && (
                <div className="rounded-xl border border-accent/20 bg-accent/5 px-4 py-3 text-center text-sm">
                  Dev OTP · <span className="font-mono font-semibold">{mockOtp}</span>
                </div>
              )}
              <div>
                <Label htmlFor="otp">One-time code</Label>
                <Input
                  id="otp"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  placeholder="6-digit code"
                  maxLength={6}
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  className="tracking-[0.3em]"
                />
              </div>
              <Button
                className="w-full"
                variant="accent"
                size="lg"
                disabled={loading || otp.length < 6}
                onClick={verifyOtp}
              >
                Verify & continue
              </Button>
              <button
                type="button"
                className="w-full text-center text-xs font-medium text-muted-foreground hover:text-foreground"
                onClick={() => setSent(false)}
              >
                Change number
              </button>
            </>
          )}

          <div className="relative py-1">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-card-border" />
            </div>
            <div className="relative flex justify-center text-[11px] uppercase tracking-[0.14em]">
              <span className="bg-card px-3 text-muted-foreground">or</span>
            </div>
          </div>

          <Button
            variant="outline"
            className="w-full"
            size="lg"
            disabled={loading}
            onClick={continueWithGoogle}
          >
            Continue with Google
          </Button>
          <p className="text-center text-[11px] text-muted-foreground">
            Dev mode uses a mock Google identity until CLIENT_ID is configured.
          </p>

          <p className="text-center text-xs text-muted-foreground">
            Or{" "}
            <Link href="/report" className="font-medium text-accent hover:underline">
              report anonymously
            </Link>
          </p>
        </Card>
      </motion.div>
    </div>
  );
}
