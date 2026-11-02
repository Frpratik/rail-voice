import type { Metadata, Viewport } from "next";
import { Toaster } from "sonner";
import { AppHeader, BottomNav, SiteFooter } from "@/components/layout/app-shell";
import { AskWidget } from "@/components/ai/ask-widget";
import { AuthGate } from "@/components/auth-gate";
import { AppSettings } from "@/providers/app-settings";
import { QueryProvider } from "@/providers/query-provider";
import { ThemeProvider } from "@/providers/theme-provider";
// Fonts ship with the app, so builds never depend on downloading them from Google.
import "@fontsource/barlow/400.css";
import "@fontsource/barlow/500.css";
import "@fontsource/barlow/600.css";
import "@fontsource/barlow-condensed/500.css";
import "@fontsource/barlow-condensed/600.css";
import "@fontsource/barlow-condensed/700.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/500.css";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "RailVoice",
    template: "%s · RailVoice",
  },
  description:
    "Community problem reporting and grievance escalation platform for Western Railway (Churchgate to Virar).",
  manifest: "/manifest.json",
  icons: { icon: "/icon.svg", apple: "/icon.svg" },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#10275c" },
    { media: "(prefers-color-scheme: dark)", color: "#0a1124" },
  ],
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-scroll-behavior="smooth" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <ThemeProvider>
          <QueryProvider>
            <AppSettings />
            <AuthGate>
              <div className="flex min-h-screen flex-col">
                <AppHeader />
                <main className="mx-auto w-full max-w-6xl flex-1 min-w-0 px-4 pb-10 pt-5 sm:px-6 md:pt-8 lg:pb-12">
                  {children}
                </main>
                <SiteFooter />
                <BottomNav />
              </div>
              <AskWidget />
              <Toaster
                position="top-center"
                richColors
                closeButton
                toastOptions={{
                  className: "font-sans!",
                }}
              />
            </AuthGate>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
