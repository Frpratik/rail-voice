"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "./types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  anonymousSessionId: string | null;
  setAuth: (user: User, token: string, refreshToken?: string) => void;
  setAnonymous: (sessionId: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      anonymousSessionId: null,
      setAuth: (user, token, refreshToken?: string) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", token);
          if (refreshToken) localStorage.setItem("refresh_token", refreshToken);
          localStorage.removeItem("anonymous_session_id");
        }
        set({ user, accessToken: token, anonymousSessionId: null });
      },
      setAnonymous: (sessionId) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("anonymous_session_id", sessionId);
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
        }
        set({ user: null, accessToken: null, anonymousSessionId: sessionId });
      },
      logout: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          localStorage.removeItem("anonymous_session_id");
        }
        set({ user: null, accessToken: null, anonymousSessionId: null });
      },
    }),
    { name: "railvoice-auth" }
  )
);
