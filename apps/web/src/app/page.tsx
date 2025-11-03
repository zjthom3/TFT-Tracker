'use client';

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AssetCard, type AssetCardProps } from "@/components/AssetCard";
import { WatchlistPanel } from "@/components/WatchlistPanel";
import { ExplainModal } from "@/components/ExplainModal";
import type { PhaseState } from "@/types/phase";



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
const PHASE_ALERTS_ENABLED = process.env.NEXT_PUBLIC_PHASE_ALERTS !== "false";
const ANALYTICS_ENDPOINT = process.env.NEXT_PUBLIC_ANALYTICS_URL ?? "";

export default function HomePage() {
  const [phaseStates, setPhaseStates] = useState<PhaseState[]>([]);
  const [marketSnapshots, setMarketSnapshots] = useState<MarketSnapshot[]>([]);
  const [indicatorSnapshots, setIndicatorSnapshots] = useState<IndicatorSnapshot[]>([]);
  const [assetDirectory, setAssetDirectory] = useState<{ ticker: string; display_ticker?: string | null; name?: string | null; type?: string | null }[]>([]);
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [addBusy, setAddBusy] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [phaseAlerts, setPhaseAlerts] = useState<{ ticker: string; from: string | null; to: string; computedAt: string }[]>([]);
const [displayOverrides, setDisplayOverrides] = useState<Record<string, string>>({});
const [modalTicker, setModalTicker] = useState<string | null>(null);
const [sessionToken, setSessionToken] = useState<string | null>(null);
const [sessionReady, setSessionReady] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const existing = window.localStorage.getItem("tft-session-token");
    if (existing) {
      setSessionToken(existing);
      setSessionReady(true);
      return;
    }
    const createSession = async () => {
      try {
        const response = await fetch(`${API_BASE}/auth/guest`, { method: "POST" });
        if (!response.ok) {
          throw new Error("Failed to create guest session");
        }
        const data = (await response.json()) as { session_token: string };
        window.localStorage.setItem("tft-session-token", data.session_token);
        setSessionToken(data.session_token);
      } catch (err) {
        console.error("Unable to create session", err);
        setFeedback({ type: "error", message: "Unable to create session." });
      } finally {
        setSessionReady(true);
      }
    };
    createSession();
  }, []);
  const phaseMapRef = useRef<Record<string, string>>({});

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
    const storedDisplay = window.localStorage.getItem("tft-watchlist-display");
    if (storedDisplay) {
      try {
        const parsed = JSON.parse(storedDisplay) as Record<string, string>;
        if (parsed && typeof parsed === "object") {
          const normalized: Record<string, string> = {};
          Object.entries(parsed).forEach(([key, value]) => {
            if (key && value) {
              normalized[key.toUpperCase()] = value.toUpperCase();
            }
          });
          setDisplayOverrides(normalized);
        }
      } catch (err) {
        console.warn("Failed to parse watchlist display overrides", err);
      }
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated || typeof window === "undefined") return;
    window.localStorage.setItem("tft-watchlist", JSON.stringify(watchlist));
  }, [hydrated, watchlist]);

  useEffect(() => {
    if (!hydrated || typeof window === "undefined") return;
    window.localStorage.setItem("tft-watchlist-display", JSON.stringify(displayOverrides));
  }, [displayOverrides, hydrated]);

  const authorizedFetch = useCallback(
    async (input: RequestInfo | URL, init: RequestInit = {}) => {
      if (!sessionReady) {
        throw new Error("Session not ready");
      }
      const headers = new Headers(init.headers as HeadersInit | undefined);
      if (sessionToken) {
        headers.set("X-Session-Token", sessionToken);
      }
      return fetch(input, { ...init, headers });
    },
    [sessionReady, sessionToken]
  );

  const track = useCallback((event: string, payload: Record<string, unknown>) => {
    const body = { event, payload, timestamp: new Date().toISOString() };
    if (process.env.NODE_ENV !== "production") {
      console.debug(`[analytics] ${event}`, payload);
    }
    if (!ANALYTICS_ENDPOINT) return;
    const json = JSON.stringify(body);
    if (typeof navigator !== "undefined" && typeof navigator.sendBeacon === "function") {
      navigator.sendBeacon(ANALYTICS_ENDPOINT, json);
    } else {
      void fetch(ANALYTICS_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: json,
        keepalive: true
      });
    }
  }, []);

  const loadAssetsDirectory = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/assets`);
      if (!response.ok) return;
      const payload = (await response.json()) as {
        ticker: string;
        display_ticker?: string | null;
        name?: string | null;
        type?: string | null;
      }[];
      const normalized = payload.map((entry) => ({
        ...entry,
        ticker: entry.ticker.toUpperCase(),
        display_ticker: entry.display_ticker?.toUpperCase() ?? entry.ticker.toUpperCase()
      }));
      setAssetDirectory(normalized);
    } catch (err) {
      console.warn("Failed to load asset directory", err);
    }
  }, []);

  const fetchWatchlist = useCallback(async () => {
    if (!sessionToken) return;
    try {
      const response = await authorizedFetch(`${API_BASE}/watchlist`);
      if (!response.ok) {
        throw new Error("Failed to load watchlist");
      }
      const payload = (await response.json()) as {
        ticker: string;
        display_ticker?: string | null;
        name?: string | null;
        type: string;
      }[];
      if (payload.length === 0) {
        setWatchlist([]);
        return;
      }
      const canonicalTickers = payload.map((item) => item.ticker.toUpperCase());
      const overrides: Record<string, string> = {};
      payload.forEach((item) => {
        if (item.display_ticker && item.display_ticker.toUpperCase() !== item.ticker.toUpperCase()) {
          overrides[item.ticker.toUpperCase()] = item.display_ticker.toUpperCase();
        }
      });
      setDisplayOverrides((prev) => ({ ...prev, ...overrides }));
      setWatchlist(canonicalTickers);
    } catch (err) {
      console.error("Unable to load watchlist", err);
      setFeedback({ type: "error", message: "Unable to load saved watchlist." });
    }
  }, [authorizedFetch, sessionToken]);

  useEffect(() => {
    loadAssetsDirectory();
  }, [loadAssetsDirectory]);

  useEffect(() => {
    if (!sessionToken) return;
    fetchWatchlist();
  }, [fetchWatchlist, sessionToken]);

  const triggerIngest = useCallback(
    async (tickers: string[]) => {
      if (!sessionReady) return;
      try {
        const response = await authorizedFetch(`${API_BASE}/ingest/run`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tickers })
        });
        if (!response.ok) {
          throw new Error(`Ingest failed (${response.status})`);
        }
      } catch (err) {
        console.error("Failed to trigger ingest", err);
        setFeedback({ type: "error", message: "Unable to trigger ingest for new ticker." });
      }
    },
    [authorizedFetch, sessionReady]
  );

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      if (watchlist.length === 0) {
        setPhaseStates([]);
        setMarketSnapshots([]);
        setIndicatorSnapshots([]);
        setError(null);
        phaseMapRef.current = {};
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

      if (phasePayload.length) {
        setDisplayOverrides((prev) => {
          let changed = false;
          const next = { ...prev };
          phasePayload.forEach((entry) => {
            if (entry.display_ticker && entry.display_ticker !== entry.ticker && !next[entry.ticker]) {
              next[entry.ticker] = entry.display_ticker.toUpperCase();
              changed = true;
            }
          });
          return changed ? next : prev;
        });
      }

      if (PHASE_ALERTS_ENABLED) {
        const previousMap = phaseMapRef.current;
        const changes = phasePayload
          .filter((entry) => {
            const previousPhase = previousMap[entry.ticker];
            return previousPhase && previousPhase !== entry.phase;
          })
          .map((entry) => ({
            ticker: entry.ticker,
            from: phaseMapRef.current[entry.ticker],
            to: entry.phase,
            computedAt: entry.computed_at
          }));

        if (changes.length) {
          setPhaseAlerts((prev) => [...changes, ...prev].slice(0, 5));
          changes.forEach((change) => track("phase_change", change));
        }
      }

      phaseMapRef.current = Object.fromEntries(phasePayload.map((entry) => [entry.ticker, entry.phase]));

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
  }, [track, watchlist]);

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

  useEffect(() => {
    if (!phaseAlerts.length) return;
    const timeout = setTimeout(() => setPhaseAlerts((prev) => prev.slice(0, Math.max(prev.length - 1, 0))), 5000);
    return () => clearTimeout(timeout);
  }, [phaseAlerts]);

  const ensureAssetExists = useCallback(async (ticker: string) => {
    if (!sessionReady) throw new Error("Session not ready");
    try {
      const response = await authorizedFetch(`${API_BASE}/assets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker,
          type: ticker.includes("-") ? "crypto" : "stock"
        })
      });
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Asset registration failed");
      }
      const data = await response.json();
      return data as { ticker: string; display_ticker?: string | null };
    } catch (err) {
      throw err instanceof Error ? err : new Error("Asset registration failed");
    }
  }, [authorizedFetch, sessionReady]);

  const handleAddTicker = useCallback(
    async (inputTicker: string) => {
      const rawTicker = inputTicker.trim().toUpperCase();
      if (!rawTicker) return;
      if (!/^[-A-Z0-9\.]{1,18}$/.test(rawTicker)) {
        setFormError("Ticker should be alphanumeric (dashes and dots allowed).");
        return;
      }

      setAddBusy(true);
      setFormError(null);
      try {
        const asset = await ensureAssetExists(rawTicker);
        const canonicalTicker = asset.ticker.toUpperCase();
        if (watchlist.includes(canonicalTicker)) {
          setFormError(`${canonicalTicker} is already on your watchlist.`);
          return;
        }

        const displayTicker = asset.display_ticker?.toUpperCase() ?? rawTicker;

        const addResponse = await authorizedFetch(`${API_BASE}/watchlist`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ticker: rawTicker })
        });
        if (!addResponse.ok) {
          const message = await addResponse.text();
          throw new Error(message || "Unable to persist watchlist item");
        }
        setWatchlist((prev) => [...prev, canonicalTicker]);
        if (displayTicker !== canonicalTicker) {
          setDisplayOverrides((prev) => ({ ...prev, [canonicalTicker]: displayTicker }));
        }

        setFeedback({ type: "success", message: `${displayTicker} added to watchlist.` });
        track("watchlist_add", { input: rawTicker, canonical: canonicalTicker });
        await triggerIngest([canonicalTicker]);
        await loadData();
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unable to add ticker.";
        setFormError(message);
        setFeedback({ type: "error", message });
      } finally {
        setAddBusy(false);
      }
    },
    [authorizedFetch, ensureAssetExists, loadData, track, triggerIngest, watchlist]
  );

  const handleRemoveTicker = useCallback(
    (ticker: string) => {
      setWatchlist((prev) => prev.filter((item) => item !== ticker));
      track("watchlist_remove", { ticker });
      setFeedback({ type: "success", message: `${ticker} removed from watchlist.` });
      setDisplayOverrides((prev) => {
        if (!(ticker in prev)) return prev;
        const { [ticker]: _ignored, ...rest } = prev;
        return rest;
      });
      if (!sessionToken) return;
      void authorizedFetch(`${API_BASE}/watchlist/${ticker}`, {
        method: "DELETE"
      }).catch((err) => {
        console.error("Failed to remove watchlist item", err);
        setFeedback({ type: "error", message: "Unable to sync removal." });
      });
    },
    [authorizedFetch, sessionToken, track]
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
        if (sessionToken) {
          void authorizedFetch(`${API_BASE}/watchlist/order`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tickers: next })
          }).catch((err) => {
            console.error("Failed to reorder watchlist", err);
            setFeedback({ type: "error", message: "Unable to update order." });
          });
        }
        track("watchlist_move", { ticker, direction });
        return next;
      });
    },
    [authorizedFetch, sessionToken, track]
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
      const displayTicker =
        displayOverrides[ticker] ??
        (phase?.display_ticker ? phase.display_ticker.toUpperCase() : undefined) ??
        (assetDirectoryMap[ticker]?.display_ticker
          ? assetDirectoryMap[ticker]?.display_ticker?.toUpperCase()
          : undefined);

      return {
        ticker,
        displayTicker: displayTicker ?? ticker,
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
        sentimentScore: phase?.sentiment_score ?? null,
        sentimentDelta: phase?.sentiment_delta ?? null,
        updatedAt: phase?.computed_at ?? market?.as_of ?? null
      } satisfies AssetCardProps;
    });
  }, [assetDirectoryMap, displayOverrides, indicatorByTicker, marketByTicker, phaseByTicker, watchlist]);

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

      {phaseAlerts.length > 0 && (
        <div className="space-y-2" aria-live="polite">
          {phaseAlerts.map((alert, index) => (
            <div
              key={`${alert.ticker}-${alert.computedAt}-${index}`}
              className="rounded-xl border border-coop/40 bg-coop/10 p-4 text-sm text-coop shadow-[0_0_20px_theme(colors.coop/15)]"
            >
              <strong className="font-mono">{alert.ticker}</strong> transitioned from {alert.from ?? "UNKNOWN"} → {alert.to}
              <span className="ml-2 text-xs text-neutral-500">{new Date(alert.computedAt).toLocaleTimeString()}</span>
            </div>
          ))}
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
        busy={addBusy || !sessionReady}
        error={formError}
        displayOverrides={displayOverrides}
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
            <AssetCard key={card.ticker} {...card} onExplain={setModalTicker} />
          ))}
        </section>
      )}
      {modalTicker && <ExplainModal ticker={modalTicker} onClose={() => setModalTicker(null)} />}
    </main>
  );
}
