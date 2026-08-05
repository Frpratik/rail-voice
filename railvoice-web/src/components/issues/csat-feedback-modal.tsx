'use client';

import React, { useState } from 'react';
import { Star, AlertCircle, CheckCircle2, RotateCcw, MessageSquare, Send } from 'lucide-react';

interface CSATFeedbackModalProps {
  issueId: string;
  currentStatus?: string;
  onFeedbackSubmitted?: (newStatus: string) => void;
}

export function CSATFeedbackModal({ issueId, onFeedbackSubmitted }: CSATFeedbackModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [rating, setRating] = useState<number>(5);
  const [hoverRating, setHoverRating] = useState<number | null>(null);
  const [comments, setComments] = useState('');
  const [isReopened, setIsReopened] = useState(false);
  const [reopenReason, setReopenReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submittedData, setSubmittedData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isReopened && reopenReason.trim().length < 5) {
      setError('Please provide a reason with at least 5 characters for reopening the issue.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const res = await fetch(`${apiBase}/issues/${issueId}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rating,
          comments: comments.trim() || undefined,
          is_reopened: isReopened,
          reopen_reason: isReopened ? reopenReason.trim() : undefined,
        }),
      });

      const json = await res.json();
      if (!res.ok) {
        throw new Error(json.detail || 'Failed to submit feedback');
      }

      setSubmittedData(json.data);
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted(json.data.new_status);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred while submitting feedback');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="my-6 rounded-2xl border border-indigo-500/20 bg-slate-900/80 p-5 backdrop-blur-xl shadow-xl">
      {!submittedData ? (
        <>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30">
                <Star className="h-5 w-5 fill-amber-400" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-100">Rate Resolution Quality</h3>
                <p className="text-xs text-slate-400">Help us maintain high maintenance standards across Indian Railways</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="rounded-lg bg-indigo-600/30 px-3 py-1.5 text-xs font-medium text-indigo-300 hover:bg-indigo-600/50 transition-all border border-indigo-500/30"
            >
              {isOpen ? 'Close Form' : 'Give Feedback'}
            </button>
          </div>

          {isOpen && (
            <form onSubmit={handleSubmit} className="mt-5 border-t border-slate-800 pt-4 space-y-4">
              {/* Star Rating */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-2">Satisfaction Rating</label>
                <div className="flex items-center gap-2">
                  {[1, 2, 3, 4, 5].map((star) => {
                    const active = (hoverRating !== null ? hoverRating : rating) >= star;
                    return (
                      <button
                        key={star}
                        type="button"
                        onClick={() => {
                          setRating(star);
                          if (star <= 2) setIsReopened(true);
                        }}
                        onMouseEnter={() => setHoverRating(star)}
                        onMouseLeave={() => setHoverRating(null)}
                        className="p-1 transition-transform hover:scale-125 focus:outline-none"
                      >
                        <Star
                          className={`h-7 w-7 transition-colors ${
                            active ? 'fill-amber-400 text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.5)]' : 'text-slate-600'
                          }`}
                        />
                      </button>
                    );
                  })}
                  <span className="ml-3 text-sm font-semibold text-amber-400">
                    {rating === 5 ? 'Excellent' : rating === 4 ? 'Good' : rating === 3 ? 'Average' : rating === 2 ? 'Poor' : 'Unsatisfactory'}
                  </span>
                </div>
              </div>

              {/* Optional Comments */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Comments (Optional)</label>
                <div className="relative">
                  <MessageSquare className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                  <textarea
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    placeholder="Provide additional details about the resolution..."
                    rows={2}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950/60 pl-9 pr-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* Reopen Toggle */}
              <div className="rounded-xl border border-rose-500/20 bg-rose-950/10 p-3">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isReopened}
                    onChange={(e) => setIsReopened(e.target.checked)}
                    className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-rose-500 focus:ring-rose-500"
                  />
                  <div className="flex items-center gap-2 text-xs font-medium text-rose-300">
                    <RotateCcw className="h-4 w-4 text-rose-400" />
                    <span>Issue remains unresolved — Reopen Grievance (+25.0 Priority Boost)</span>
                  </div>
                </label>

                {isReopened && (
                  <div className="mt-3">
                    <input
                      type="text"
                      value={reopenReason}
                      onChange={(e) => setReopenReason(e.target.value)}
                      placeholder="Specify why this issue needs to be reopened..."
                      className="w-full rounded-lg border border-rose-500/30 bg-slate-950/80 px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-rose-500 focus:outline-none"
                    />
                  </div>
                )}
              </div>

              {error && (
                <div className="flex items-center gap-2 rounded-lg bg-rose-500/10 p-2.5 text-xs text-rose-400 border border-rose-500/20">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 py-2.5 text-sm font-semibold text-slate-950 hover:from-amber-400 hover:to-amber-500 transition-all disabled:opacity-50 shadow-lg shadow-amber-500/20"
              >
                <Send className="h-4 w-4" />
                {submitting ? 'Submitting Feedback...' : 'Submit Resolution CSAT'}
              </button>
            </form>
          )}
        </>
      ) : (
        <div className="flex items-center gap-3 text-emerald-400">
          <CheckCircle2 className="h-6 w-6 shrink-0" />
          <div>
            <h4 className="font-semibold text-slate-100">Thank you for your feedback!</h4>
            <p className="text-xs text-slate-400">
              {submittedData.is_reopened
                ? 'Grievance has been reopened and dispatched to station administration with elevated priority (+25.0).'
                : `Your ${submittedData.rating}-star rating has been registered on the vendor scorecard.`}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
