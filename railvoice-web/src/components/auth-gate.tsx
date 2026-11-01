"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import type { User } from "@/lib/types";

const PUBLIC_PATHS = ["/login", "/help", "/privacy", "/terms"];

function isPublicPath(pathname: string) {
  return PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

export function AuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const setAuth = useAuthStore((state) => state.setAuth);
  const logout = useAuthStore((state) => state.logout);
  const checkedSession = useRef(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    // Deferred so the already-hydrated case doesn't set state synchronously in the effect.
    if (useAuthStore.persist.hasHydrated()) queueMicrotask(() => setHydrated(true));
    return useAuthStore.persist.onFinishHydration(() => setHydrated(true));
  }, []);
  const [sessionValid, setSessionValid] = useState(false);

  useEffect(() => {
    if (!hydrated) return;
    if (isPublicPath(pathname)) return;
    if (!user) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }
    if (checkedSession.current) return;

    checkedSession.current = true;
    void api.users
      .me()
      .then((response) => {
        const token = localStorage.getItem("access_token");
        if (!token) throw new Error("Session expired");
        setAuth(
          {
            id: response.data.id,
            display_name: response.data.display_name,
            is_verified: response.data.is_verified,
            is_anonymous: response.data.is_anonymous,
            roles: response.data.roles,
            persona: response.data.persona as User["persona"],
            persona_label: response.data.persona_label,
          },
          token
        );
        setSessionValid(true);
      })
      .catch(() => {
        logout();
        router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      });
  }, [hydrated, logout, pathname, router, setAuth, user]);

  if (isPublicPath(pathname)) return children;
  if (!hydrated || !sessionValid || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        Checking your session…
      </div>
    );
  }

  return children;
}
