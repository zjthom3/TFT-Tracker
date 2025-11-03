'use client';

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { AssetCard, type AssetCardProps } from "@/components/AssetCard";
import { WatchlistPanel } from "@/components/WatchlistPanel";

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
  const [assetDirectory, setAssetDirectory] = useState<{ ticker: string; name?: string | null; type?: string | null }[]>([]);
  const [watchlist, setWatchlist] = useState<string[]>(["NVDA", "BTC-USD"]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [addBusy, setAddBusy] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = window.localStorage.getItem("tft-watchlist");
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as string[];
        if (Array.isArray(parsed) && parsed.length > 0) {
          setWatchlist(parsed.map((ticker) => ticker.toUpperCase()));
        }
      } catch (err) {
        console.warn("Failed to parse watchlist from storage", err);
      }
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated || typeof window === "undefined") return;
    window.localStorage.setItem("tft-watchlist", JSON.stringify(watchlist));
  }, [hydrated, watchlist]);

  const track = useCallback((event: string, payload: Record<string, unknown>) => {
    if (process.env.NODE_ENV !== "production") {
      console.debug(`[analytics] ${event}`, payload);
    }
  }, []);

  const loadAssetsDirectory = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/assets`);
      if (!response.ok) return;
      const payload = (await response.json()) as { ticker: string; name?: string | null; type?: string | null }[];
      setAssetDirectory(payload);
    } catch (err) {
      console.warn("Failed to load asset directory", err);
    }
  }, []);

  useEffect(() => {
    loadAssetsDirectory();
  }, [loadAssetsDirectory]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      if (watchlist.length === 0) {
        setPhaseStates([]);
        setMarketSnapshots([]);
        setIndicatorSnapshots([]);
        setError(null);
        return;
      }

      const query = watchlist.map((ticker) => `tickers=${encodeURIComponent(ticker)}`).join("&");
      const [phaseRes, marketRes, indicatorRes] = await Promise.all([
        fetch(`${API_BASE}/phase?${query}`),
        fetch(`${API_BASE}/snapshots/latest?${query}`),
        fetch(`${API_BASE}/indicators/latest?${query}`)
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
  }, [watchlist]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60_000);
    return () => clearInterval(interval);
  }, [loadData]);

  useEffect(() => {
    if (!feedback) return;
    const timeout = setTimeout(() => setFeedback(null), 4000);
    return () => clearTimeout(timeout);
  }, [feedback]);

  const ensureAssetExists = useCallback(async (ticker: string) => {
    try {
      const response = await fetch(`${API_BASE}/assets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker,
          type: ticker.includes("-") ? "crypto" : "stock"
        })
      });
      if (!response.ok && response.status !== 409) {
        const message = await response.text();
        throw new Error(message || "Asset registration failed");
      }
    } catch (err) {
      throw err instanceof Error ? err : new Error("Asset registration failed");
    }
  }, []);

  const handleAddTicker = useCallback(
    async (inputTicker: string) => {
      const ticker = inputTicker.trim().toUpperCase();
      if (!ticker) return;
      if (!/^[-A-Z0-9\.]{1,12}$/.test(ticker)) {
        setFormError("Ticker should be alphanumeric (dashes and dots allowed).");
        return;
      }
      if (watchlist.includes(ticker)) {
        setFormError(`${ticker} is already on your watchlist.`);
        return;
      }

      setAddBusy(true);
      setFormError(null);
      try {
        await ensureAssetExists(ticker);
        setWatchlist((prev) => [...prev, ticker]);
        setFeedback({ type: "success", message: `${ticker} added to watchlist.` });
        track("watchlist_add", { ticker });
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unable to add ticker.";
        setFormError(message);
        setFeedback({ type: "error", message });
      } finally {
        setAddBusy(false);
      }
    },
    [ensureAssetExists, track, watchlist]
  );

  const handleRemoveTicker = useCallback(
    (ticker: string) => {
      setWatchlist((prev) => prev.filter((item) => item !== ticker));
      track("watchlist_remove", { ticker });
      setFeedback({ type: "success", message: `${ticker} removed from watchlist.` });
    },
    [track]
  );

  const handleMoveTicker = useCallback(
    (ticker: string, direction: "up" | "down") => {
      setWatchlist((prev) => {
        const index = prev.indexOf(ticker);
        if (index === -1) return prev;
        const targetIndex = direction === "up" ? index - 1 : index + 1;
        if (targetIndex < 0 || targetIndex >= prev.length) return prev;
        const next = [...prev];
        [next[index], next[targetIndex]] = [next[targetIndex], next[index]];
        return next;
      });
      track("watchlist_move", { ticker, direction });
    },
    [track]
  );

  const marketByTicker = useMemo(
    () => Object.fromEntries(marketSnapshots.map((item) => [item.ticker, item])),
    [marketSnapshots]
  );
  const indicatorByTicker = useMemo(
    () => Object.fromEntries(indicatorSnapshots.map((item) => [item.ticker, item])),
    [indicatorSnapshots]
  );
  const phaseByTicker = useMemo(
    () => Object.fromEntries(phaseStates.map((item) => [item.ticker, item])),
    [phaseStates]
  );

  const assetDirectoryMap = useMemo(
    () => Object.fromEntries(assetDirectory.map((entry) => [entry.ticker, entry])),
    [assetDirectory]
  );

  const cards: AssetCardProps[] = useMemo(() => {
    return watchlist.map((ticker) => {
      const phase = phaseByTicker[ticker];
      const market = marketByTicker[ticker];
      const indicator = indicatorByTicker[ticker];
      const awaitingData = !phase;

      return {
        ticker,
        name: phase?.asset_name ?? assetDirectoryMap[ticker]?.name ?? null,
        phase: awaitingData ? "AWAITING" : phase.phase,
        confidence: phase?.confidence ?? null,
        rationale: phase?.rationale ?? null,
        statusMessage: awaitingData
          ? "Awaiting market data. Trigger an ingest run to compute the first phase."
          : null,
        price: market?.price ?? null,
        priceChangePct: market?.price_change_pct ?? null,
        volatility: market?.volatility_1d ?? null,
        rsi: indicator?.rsi_14 ?? null,
        updatedAt: phase?.computed_at ?? market?.as_of ?? null
      } satisfies AssetCardProps;
    });
  }, [assetDirectoryMap, indicatorByTicker, marketByTicker, phaseByTicker, watchlist]);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-8 px-6 py-12">
      <section className="rounded-2xl border border-neutral-700 bg-neutral-900/60 p-8 shadow-xl backdrop-blur">
        <div className="flex flex-col gap-2">
          <span className="text-sm uppercase tracking-wide text-neutral-400">Sprint 3</span>
          <h1 className="text-4xl font-semibold text-neutral-100">Tit-for-Tat Asset Tracker</h1>
          <p className="text-neutral-300">
            Manage a personalized watchlist, view live phase indicators, and keep pulse on asset sentiment.
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
              className="rounded-full border border-neutral-700 px-4 py-1 font-medium text-neutral-200 hover:border-neutral-500 focus:outline-none focus:ring-2 focus:ring-coop/40"
            >
              Refresh data
            </button>
          </div>
        </div>
      </section>

      {feedback && (
        <div
          role="status"
          aria-live="polite"
          className={`rounded-xl border ${
            feedback.type === "success"
              ? "border-coop/40 bg-coop/10 text-coop"
              : "border-red-500/40 bg-red-500/10 text-red-200"
          } p-4 text-sm`}
        >
          {feedback.message}
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
          {error}
        </div>
      )}

      <WatchlistPanel
        watchlist={watchlist}
        assetDirectory={assetDirectory}
        onAdd={handleAddTicker}
        onRemove={handleRemoveTicker}
        onMove={handleMoveTicker}
        busy={addBusy}
        error={formError}
      />

      {loading ? (
        <section className="grid gap-6 sm:grid-cols-2">
          {[...Array(4)].map((_, idx) => (
            <div key={idx} className="h-52 animate-pulse rounded-2xl border border-neutral-800 bg-neutral-900/60" />
          ))}
        </section>
      ) : watchlist.length === 0 ? (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-8 text-center text-neutral-300">
          Add a ticker to your watchlist to start tracking phases.
        </div>
      ) : (
        <section className="grid gap-6 md:grid-cols-2">
          {cards.map((card) => (
            <AssetCard key={card.ticker} {...card} />
          ))}
        </section>
      )}
    </main>
  );
}
