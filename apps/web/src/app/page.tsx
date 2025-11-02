'use client';

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { AssetCard, type AssetCardProps } from "@/components/AssetCard";

type PhaseState = {
  ticker: string;
  asset_name?: string | null;
  asset_type: string;
  phase: string;
  confidence?: number | null;
  rationale?: string | null;
  computed_at: string;
};

type MarketSnapshot = {
  ticker: string;
  price?: number | null;
  price_change_pct?: number | null;
  volatility_1d?: number | null;
  as_of: string;
};

type IndicatorSnapshot = {
  ticker: string;
  rsi_14?: number | null;
  as_of: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export default function HomePage() {
  const [phaseStates, setPhaseStates] = useState<PhaseState[]>([]);
  const [marketSnapshots, setMarketSnapshots] = useState<MarketSnapshot[]>([]);
  const [indicatorSnapshots, setIndicatorSnapshots] = useState<IndicatorSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [phaseRes, marketRes, indicatorRes] = await Promise.all([
        fetch(`${API_BASE}/phase`),
        fetch(`${API_BASE}/snapshots/latest`),
        fetch(`${API_BASE}/indicators/latest`)
      ]);

      if (!phaseRes.ok || !marketRes.ok || !indicatorRes.ok) {
        throw new Error("Failed to load data from API");
      }

      const phasePayload = (await phaseRes.json()) as PhaseState[];
      const marketPayload = (await marketRes.json()) as MarketSnapshot[];
      const indicatorPayload = (await indicatorRes.json()) as IndicatorSnapshot[];

      setPhaseStates(phasePayload);
      setMarketSnapshots(marketPayload);
      setIndicatorSnapshots(indicatorPayload);
      setError(null);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60_000);
    return () => clearInterval(interval);
  }, [loadData]);

  const cards: AssetCardProps[] = useMemo(() => {
    const marketByTicker = Object.fromEntries(marketSnapshots.map((item) => [item.ticker, item]));
    const indicatorByTicker = Object.fromEntries(indicatorSnapshots.map((item) => [item.ticker, item]));

    return phaseStates
      .map((phase) => {
        const market = marketByTicker[phase.ticker];
        const indicator = indicatorByTicker[phase.ticker];
        const updatedAt = market?.as_of ?? phase.computed_at;

        return {
          ticker: phase.ticker,
          name: phase.asset_name,
          phase: phase.phase,
          confidence: phase.confidence,
          rationale: phase.rationale,
          price: market?.price ?? null,
          priceChangePct: market?.price_change_pct ?? null,
          volatility: market?.volatility_1d ?? null,
          rsi: indicator?.rsi_14 ?? null,
          updatedAt
        } satisfies AssetCardProps;
      })
      .sort((a, b) => a.ticker.localeCompare(b.ticker));
  }, [phaseStates, marketSnapshots, indicatorSnapshots]);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-8 px-6 py-12">
      <section className="rounded-2xl border border-neutral-700 bg-neutral-900/60 p-8 shadow-xl backdrop-blur">
        <div className="flex flex-col gap-2">
          <span className="text-sm uppercase tracking-wide text-neutral-400">Sprint 2</span>
          <h1 className="text-4xl font-semibold text-neutral-100">Tit-for-Tat Asset Tracker</h1>
          <p className="text-neutral-300">
            Rule-based phase detection, live asset cards, and behavior-aware signals across your watchlist.
          </p>
          <div className="mt-4 flex flex-wrap gap-3 text-sm text-neutral-300">
            <Link className="underline-offset-4 hover:underline" href="http://localhost:8000/docs">
              OpenAPI Docs
            </Link>
            <Link className="underline-offset-4 hover:underline" href="https://github.com/zacharythomas">
              GitHub Workspace
            </Link>
            <button
              onClick={loadData}
              className="rounded-full border border-neutral-700 px-4 py-1 font-medium text-neutral-200 hover:border-neutral-500"
            >
              Refresh data
            </button>
          </div>
        </div>
      </section>

      {error && (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <section className="grid gap-6 sm:grid-cols-2">
          {[...Array(4)].map((_, idx) => (
            <div key={idx} className="h-52 animate-pulse rounded-2xl border border-neutral-800 bg-neutral-900/60" />
          ))}
        </section>
      ) : cards.length > 0 ? (
        <section className="grid gap-6 md:grid-cols-2">
          {cards.map((card) => (
            <AssetCard key={card.ticker} {...card} />
          ))}
        </section>
      ) : (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-8 text-center text-neutral-300">
          No phase data available yet. Trigger an ingest run to populate market indicators.
        </div>
      )}
    </main>
  );
}
