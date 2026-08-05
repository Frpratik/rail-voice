"use client";

import { useCallback, useEffect, useState } from "react";
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
import { DEMO_ACCOUNTS, isOpsPersona, resolvePersona } from "@/lib/roles";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";
const ALLOW_MOCK_GOOGLE =
  process.env.NEXT_PUBLIC_GOOGLE_MOCK !== "false" && !GOOGLE_CLIENT_ID;
const SHOW_DEMO_ACCOUNTS = process.env.NEXT_PUBLIC_OTP_MOCK !== "false";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string }) => void;
          }) => void;
          prompt: () => void;
          renderButton: (
            parent: HTMLElement,
            options: Record<string, unknown>
          ) => void;
        };
      };
    };
  }
}

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [mobile, setMobile] = useState("+91");
  const [otp, setOtp] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [mockOtp, setMockOtp] = useState<string | null>(null);
  const [googleReady, setGoogleReady] = useState(false);

  const finishLogin = useCallback(
    (
      user: {
        roles: string[];
        persona?: string;
      },
      access: string,
      refresh?: string,
      preferredHome?: string
    ) => {
      setAuth(user as never, access, refresh);
      const persona = user.persona ?? resolvePersona(user.roles);
      const home =
        preferredHome ||
        (isOpsPersona(persona as "passenger" | "station_admin" | "main_admin")
          ? "/admin/dashboard"
          : "/");
      router.push(home);
    },
    [router, setAuth]
  );

  const finishGoogle = useCallback(
    async (idToken: string, extras?: { email?: string; name?: string; google_id?: string }) => {
      setLoading(true);
      try {
        const res = await api.auth.google({
          id_token: idToken,
          ...extras,
        });
        toast.success("Signed in with Google");
        finishLogin(res.data.user, res.data.access_token, res.data.refresh_token);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Google sign-in failed");
      } finally {
        setLoading(false);
      }
    },
    [finishLogin]
  );

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;

    const existing = document.getElementById("google-gsi");
    if (existing) {
      setTimeout(() => setGoogleReady(true), 0);
      return;
    }

    const script = document.createElement("script");
    script.id = "google-gsi";
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.onload = () => setGoogleReady(true);
    document.body.appendChild(script);
  }, []);

  useEffect(() => {
    if (!googleReady || !GOOGLE_CLIENT_ID || !window.google) return;
    const host = document.getElementById("google-btn-host");
    if (!host) return;
    host.innerHTML = "";
    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: (response) => {
        void finishGoogle(response.credential);
      },
    });
    window.google.accounts.id.renderButton(host, {
      theme: "outline",
      size: "large",
      width: host.offsetWidth || 320,
      text: "continue_with",
      shape: "rectangular",
    });
  }, [googleReady, finishGoogle]);

  const requestOtp = async () => {
    setLoading(true);
    try {
      const res = await api.auth.requestOtp(mobile);
      setSent(true);
      if (res.data.mock_otp) setMockOtp(res.data.mock_otp);
      else setMockOtp(null);
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
      toast.success("Welcome to RailVoice");
      finishLogin(res.data.user, res.data.access_token, res.data.refresh_token);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Invalid OTP");
    } finally {
      setLoading(false);
    }
  };

  const loginAsDemo = async (demo: (typeof DEMO_ACCOUNTS)[number]) => {
    setLoading(true);
    try {
      const req = await api.auth.requestOtp(demo.mobile);
      const code = req.data.mock_otp || "123456";
      const res = await api.auth.verifyOtp(demo.mobile, code);
      toast.success(`Signed in as ${demo.label}`);
      finishLogin(
        res.data.user,
        res.data.access_token,
        res.data.refresh_token,
        demo.home
      );
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Demo login failed");
    } finally {
      setLoading(false);
    }
  };

  const continueWithMockGoogle = async () => {
    await finishGoogle("mock-token", {
      email: "dev.user@railvoice.local",
      name: "Dev Google User",
      google_id: "mock-google-dev",
    });
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
              Passenger · Station Admin · Main Admin
            </p>
          </div>

          {SHOW_DEMO_ACCOUNTS && (
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                Demo accounts
              </p>
              <div className="grid gap-2">
                {DEMO_ACCOUNTS.map((demo) => (
                  <button
                    key={demo.mobile}
                    type="button"
                    disabled={loading}
                    onClick={() => void loginAsDemo(demo)}
                    className="rounded-2xl border border-card-border bg-background/60 px-4 py-3 text-left transition hover:border-accent/40 hover:bg-accent/5 disabled:opacity-60"
                  >
                    <p className="text-sm font-semibold tracking-tight">{demo.label}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{demo.description}</p>
                    <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                      {demo.mobile} · OTP 123456
                    </p>
                  </button>
                ))}
              </div>
            </div>
          )}

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

          {(GOOGLE_CLIENT_ID || ALLOW_MOCK_GOOGLE) && (
            <>
              <div className="relative py-1">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-card-border" />
                </div>
                <div className="relative flex justify-center text-[11px] uppercase tracking-[0.14em]">
                  <span className="bg-card px-3 text-muted-foreground">or</span>
                </div>
              </div>

              {GOOGLE_CLIENT_ID ? (
                <div id="google-btn-host" className="flex min-h-11 w-full justify-center" />
              ) : (
                <>
                  <Button
                    variant="outline"
                    className="w-full"
                    size="lg"
                    disabled={loading}
                    onClick={continueWithMockGoogle}
                  >
                    Continue with Google
                  </Button>
                  <p className="text-center text-[11px] text-muted-foreground">
                    Dev mode uses a mock Google identity until CLIENT_ID is configured.
                  </p>
                </>
              )}
            </>
          )}

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
