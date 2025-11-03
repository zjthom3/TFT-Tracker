"use client";

import { useEffect, useState } from "react";

import type { PhaseState } from "@/types/phase";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

type HistoryEntry = {
  id: string;
  from_phase: string | null;
  to_phase: string;
  confidence: number | null;
  rationale: string | null;
  changed_at: string;
};

type ExplainModalProps = {
  ticker: string;
  onClose: () => void;
};

export function ExplainModal({ ticker, onClose }: ExplainModalProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<PhaseState | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    let cancelled = false;
    const fetchData = async () => {
      try {
        setLoading(true);
        const [detailRes, historyRes] = await Promise.all([
          fetch(`${API_BASE}/phase/${ticker}`),
          fetch(`${API_BASE}/phase/${ticker}/history?limit=10`)
        ]);
        if (!detailRes.ok || !historyRes.ok) {
          throw new Error("Unable to load explanation");
        }
        const detailPayload = (await detailRes.json()) as PhaseState;
        const historyPayload = (await historyRes.json()) as HistoryEntry[];
        if (!cancelled) {
          setDetail(detailPayload);
          setHistory(historyPayload);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unexpected error");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    fetchData();
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" role="dialog" aria-modal="true">
      <div className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-neutral-800 bg-neutral-900 p-6 shadow-2xl">
        <header className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-neutral-100">{detail?.display_ticker ?? ticker}</h2>
            {detail?.ticker && detail?.display_ticker && detail.display_ticker !== detail.ticker && (
              <p className="text-xs uppercase tracking-wide text-neutral-500">Canonical symbol: {detail.ticker}</p>
            )}
            <p className="mt-1 text-sm text-neutral-400">Phase explanation and recent history</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-neutral-700 px-3 py-1 text-sm text-neutral-200 hover:border-neutral-500 focus:outline-none focus:ring-2 focus:ring-coop/40"
          >
            Close
          </button>
        </header>

        {loading && <p className="mt-6 text-sm text-neutral-400">Loading…</p>}
        {error && <p className="mt-6 rounded border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}

        {!loading && !error && detail && (
          <div className="mt-6 space-y-6">
            <section>
              <h3 className="text-sm uppercase tracking-wide text-neutral-500">Current Phase</h3>
              <div className="mt-2 rounded-xl border border-neutral-800 bg-neutral-950/60 p-4 text-sm text-neutral-200">
                <p>
                  <strong>{detail.phase}</strong> — confidence {detail.confidence !== null ? `${(detail.confidence * 100).toFixed(0)}%` : "--"}
                </p>
                {detail.rationale && <p className="mt-2 whitespace-pre-wrap text-neutral-300">{detail.rationale}</p>}
                {detail.sentiment_score !== null && (
                  <p className="mt-2 text-neutral-400">
                    Sentiment score {detail.sentiment_score.toFixed(2)}
                    {detail.sentiment_delta !== null && ` (Δ ${detail.sentiment_delta.toFixed(2)})`}
                  </p>
                )}
                <p className="mt-2 text-xs text-neutral-500">
                  Last computed {new Date(detail.computed_at).toLocaleString()}
                </p>
              </div>
            </section>

            <section>
              <h3 className="text-sm uppercase tracking-wide text-neutral-500">Phase History</h3>
              {history.length === 0 ? (
                <p className="mt-2 text-sm text-neutral-400">No history entries yet.</p>
              ) : (
                <ul className="mt-2 space-y-3">
                  {history.map((entry) => (
                    <li
                      key={entry.id}
                      className="rounded-xl border border-neutral-800 bg-neutral-950/60 p-4 text-sm text-neutral-200"
                    >
                      <p>
                        <strong>{entry.to_phase}</strong>
                        {entry.from_phase ? ` (from ${entry.from_phase})` : ""}
                        {entry.confidence !== null ? ` — ${(entry.confidence * 100).toFixed(0)}% confidence` : ""}
                      </p>
                      {entry.rationale && <p className="mt-2 text-neutral-300">{entry.rationale}</p>}
                      <p className="mt-2 text-xs text-neutral-500">
                        {new Date(entry.changed_at).toLocaleString()}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
