"use client";

import { FormEvent, useMemo, useState } from "react";

type AssetDirectoryEntry = {
  ticker: string;
  name?: string | null;
  type?: string | null;
};

type WatchlistPanelProps = {
  watchlist: string[];
  assetDirectory: AssetDirectoryEntry[];
  onAdd(ticker: string): Promise<void> | void;
  onRemove(ticker: string): void;
  onMove(ticker: string, direction: "up" | "down"): void;
  busy?: boolean;
  error?: string | null;
};

export function WatchlistPanel({
  watchlist,
  assetDirectory,
  onAdd,
  onRemove,
  onMove,
  busy = false,
  error
}: WatchlistPanelProps) {
  const [inputValue, setInputValue] = useState("");

  const normalizedOptions = useMemo(
    () =>
      assetDirectory.map((entry) => ({
        ticker: entry.ticker,
        label: entry.name ? `${entry.ticker} · ${entry.name}` : entry.ticker
      })),
    [assetDirectory]
  );

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!inputValue.trim()) return;
    const normalized = inputValue.trim().toUpperCase();
    await onAdd(normalized);
    setInputValue("");
  };

  return (
    <section className="rounded-2xl border border-neutral-800 bg-neutral-900/80 p-6">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-neutral-100">Watchlist</h2>
          <p className="text-sm text-neutral-400">Add assets by ticker to track Tit-for-Tat phases.</p>
        </div>
      </header>

      <form className="mt-4 flex flex-col gap-3 sm:flex-row" onSubmit={handleSubmit}>
        <div className="relative grow">
          <input
            list="watchlist-ticker-options"
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            placeholder="e.g. NVDA, BTC-USD"
            aria-label="Ticker symbol"
            autoComplete="off"
            className="w-full rounded-xl border border-neutral-700 bg-neutral-950 px-4 py-3 text-neutral-100 placeholder:text-neutral-500 focus:border-coop focus:outline-none focus:ring-2 focus:ring-coop/40"
            disabled={busy}
          />
          <datalist id="watchlist-ticker-options">
            {normalizedOptions.map((option) => (
              <option key={option.ticker} value={option.ticker} label={option.label} />
            ))}
          </datalist>
        </div>
        <button
          type="submit"
          className="rounded-xl border border-coop/70 bg-coop/20 px-5 py-3 text-sm font-semibold text-coop shadow-[0_0_20px_theme(colors.coop/20)] transition hover:bg-coop/30 disabled:cursor-not-allowed disabled:border-neutral-800 disabled:bg-neutral-900 disabled:text-neutral-600"
          disabled={busy}
        >
          {busy ? "Adding…" : "Add"}
        </button>
      </form>

      {error && <p className="mt-3 text-sm text-red-400" role="alert">{error}</p>}

      <ul className="mt-6 space-y-3">
        {watchlist.length === 0 && (
          <li className="rounded-xl border border-dashed border-neutral-700 bg-neutral-950/60 p-4 text-sm text-neutral-400">
            Your watchlist is empty. Add a ticker above to begin tracking phases.
          </li>
        )}
        {watchlist.map((ticker, index) => {
          const assetMeta = assetDirectory.find((entry) => entry.ticker === ticker);
          return (
            <li
              key={ticker}
              className="flex items-center justify-between gap-4 rounded-xl border border-neutral-800 bg-neutral-950/70 px-4 py-3"
            >
              <div>
                <span className="font-mono text-lg text-neutral-100">{ticker}</span>
                {assetMeta?.name && <p className="text-xs text-neutral-500">{assetMeta.name}</p>}
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => onMove(ticker, "up")}
                  disabled={index === 0}
                  className="rounded-lg border border-neutral-700 px-3 py-1 text-xs text-neutral-300 hover:border-neutral-500 focus:outline-none focus:ring-2 focus:ring-coop/50 disabled:cursor-not-allowed disabled:text-neutral-700"
                >
                  Move up
                </button>
                <button
                  type="button"
                  onClick={() => onMove(ticker, "down")}
                  disabled={index === watchlist.length - 1}
                  className="rounded-lg border border-neutral-700 px-3 py-1 text-xs text-neutral-300 hover:border-neutral-500 focus:outline-none focus:ring-2 focus:ring-coop/50 disabled:cursor-not-allowed disabled:text-neutral-700"
                >
                  Move down
                </button>
                <button
                  type="button"
                  onClick={() => onRemove(ticker)}
                  className="rounded-lg border border-neutral-700 px-3 py-1 text-xs text-red-300 hover:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-500/40"
                >
                  Remove
                </button>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
