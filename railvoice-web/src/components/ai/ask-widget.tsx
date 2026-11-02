"use client";

import { useQuery } from "@tanstack/react-query";
import { MessageCircleQuestion, Send, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

interface Turn {
  question: string;
  answer?: string;
  issues?: { id: string; issue_number: string; title: string }[];
  failed?: boolean;
}

/** "Ask RailVoice": a small chat that answers from the public reports and how the app works. */
export function AskWidget() {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);
  const anonymousSessionId = useAuthStore((s) => s.anonymousSessionId);
  const setAnonymous = useAuthStore((s) => s.setAnonymous);
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);
  const { data: aiStatus } = useQuery({ queryKey: ["ai-status"], queryFn: () => api.ai.status() });

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "end" });
  }, [turns]);

  if (!aiStatus?.data.enabled || pathname.startsWith("/admin") || pathname.startsWith("/embed")) return null;

  const send = async () => {
    const q = question.trim();
    if (q.length < 3 || busy) return;
    setQuestion("");
    setTurns((t) => [...t, { question: q }]);
    setBusy(true);
    try {
      if (!user && !anonymousSessionId) {
        const res = await api.auth.anonymous();
        setAnonymous(res.data.anonymous_session_id);
      }
      const res = await api.ai.ask({ question: q });
      setTurns((t) => t.map((turn, i) => (i === t.length - 1 ? { ...turn, ...res.data } : turn)));
    } catch {
      setTurns((t) => t.map((turn, i) => (i === t.length - 1 ? { ...turn, failed: true } : turn)));
    } finally {
      setBusy(false);
    }
  };

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="label-caps fixed bottom-24 right-4 z-40 inline-flex h-11 items-center gap-2 border-2 border-foreground bg-accent px-4 text-sm text-accent-foreground shadow-lg lg:bottom-6"
      >
        <MessageCircleQuestion className="h-4 w-4" />
        Ask
      </button>
    );
  }

  return (
    <div
      role="dialog"
      aria-label="Ask RailVoice"
      className="fixed inset-x-2 bottom-24 z-50 flex max-h-[70vh] flex-col border-2 border-foreground bg-card shadow-2xl sm:inset-x-auto sm:right-4 sm:w-96 lg:bottom-6"
    >
      <div className="flex items-center justify-between border-b-2 border-foreground bg-primary px-3 py-2 text-primary-foreground">
        <p className="text-display text-lg">Ask RailVoice</p>
        <button type="button" onClick={() => setOpen(false)} aria-label="Close">
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto p-3 text-sm">
        {turns.length === 0 && (
          <p className="text-muted-foreground">
            Ask about problems at a station or how reporting works, in any language. For example: &ldquo;Andheri
            escalator ka complaint hua hai kya?&rdquo;
          </p>
        )}
        {turns.map((turn, i) => (
          <div key={i} className="space-y-1.5">
            <p className="ml-8 bg-muted px-3 py-2">{turn.question}</p>
            {turn.answer !== undefined ? (
              <div className="mr-8 space-y-1.5 border-l-4 border-accent px-3 py-1">
                <p>{turn.answer}</p>
                {turn.issues?.map((issue) => (
                  <Link
                    key={issue.id}
                    href={`/issues/${issue.id}`}
                    className="block text-xs text-primary underline underline-offset-2"
                  >
                    {issue.issue_number}: {issue.title}
                  </Link>
                ))}
              </div>
            ) : turn.failed ? (
              <p className="mr-8 px-3 text-destructive">Couldn&apos;t answer right now. Please try again.</p>
            ) : (
              <p className="mr-8 px-3 text-muted-foreground">Thinking…</p>
            )}
          </div>
        ))}
        <div ref={bottom} />
      </div>
      <form
        className="flex gap-2 border-t-2 border-foreground/20 p-2"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          maxLength={500}
          placeholder="Type your question"
          aria-label="Your question"
          className="h-10 min-w-0 flex-1 border-2 border-foreground/30 bg-background px-2"
        />
        <button
          type="submit"
          disabled={busy || question.trim().length < 3}
          aria-label="Send"
          className="inline-flex h-10 w-10 items-center justify-center bg-primary text-primary-foreground disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
      <p className="px-3 pb-2 text-[11px] text-muted-foreground">Answers are written by AI from public reports. Emergencies: call 139.</p>
    </div>
  );
}
