import type { Metadata, Viewport } from "next";
import { JetBrains_Mono, Sora } from "next/font/google";
import { Toaster } from "sonner";
import { AppHeader, BottomNav, SiteFooter } from "@/components/layout/app-shell";
import { AuthGate } from "@/components/auth-gate";
import { QueryProvider } from "@/providers/query-provider";
import { ThemeProvider } from "@/providers/theme-provider";
import "./globals.css";

const sora = Sora({
  variable: "--font-sora",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const mono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: {
    default: "RailVoice",
    template: "%s · RailVoice",
  },
  description:
    "Community problem reporting and grievance escalation platform for Western Railway (Churchgate to Virar).",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f4f5f7" },
    { media: "(prefers-color-scheme: dark)", color: "#07080a" },
  ],
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${sora.variable} ${mono.variable} font-sans antialiased`}>
        <ThemeProvider>
          <QueryProvider>
            <AuthGate>
              <div className="flex min-h-screen flex-col">
                <AppHeader />
                <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-28 pt-6 sm:px-6 md:pb-12 md:pt-8">
                  {children}
                </main>
                <SiteFooter />
                <BottomNav />
              </div>
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
