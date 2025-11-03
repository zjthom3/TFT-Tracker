import { formatDistanceToNow } from "date-fns";
import { PhaseBadge } from "@/components/PhaseBadge";

export type AssetCardProps = {
  ticker: string;
  displayTicker?: string;
  name?: string | null;
  phase: string;
  confidence?: number | null;
  rationale?: string | null;
  price?: number | null;
  priceChangePct?: number | null;
  rsi?: number | null;
  updatedAt?: string | null;
  volatility?: number | null;
  statusMessage?: string | null;
  sentimentScore?: number | null;
  sentimentDelta?: number | null;
  onExplain?: (ticker: string) => void;
};

function formatNumber(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "--";
  }
  return value.toFixed(digits);
}

export function AssetCard(props: AssetCardProps) {
  const {
    ticker,
    displayTicker,
    name,
    phase,
    confidence,
    rationale,
    price,
    priceChangePct,
    rsi,
    updatedAt,
    volatility,
    statusMessage,
    sentimentScore,
    sentimentDelta,
    onExplain
  } = props;

  const updatedDistance = updatedAt
    ? formatDistanceToNow(new Date(updatedAt), { addSuffix: true })
    : "Pending ingest";

  return (
    <article className="group relative overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/70 p-6 transition-transform hover:-translate-y-1 hover:border-neutral-700 hover:shadow-xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex flex-col">
              <span className="font-mono text-2xl font-semibold text-neutral-100">{displayTicker ?? ticker}</span>
              {displayTicker && displayTicker !== ticker && (
                <span className="text-[10px] uppercase tracking-wide text-neutral-500">Canonical: {ticker}</span>
              )}
            </div>
            <PhaseBadge phase={phase} />
          </div>
          {name && <p className="mt-1 text-sm text-neutral-400">{name}</p>}
        </div>
        <div className="text-right">
          <p className="text-sm text-neutral-500">Confidence</p>
          <p className="text-lg font-semibold text-neutral-100">
            {confidence !== undefined && confidence !== null ? `${(confidence * 100).toFixed(0)}%` : "--"}
          </p>
        </div>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-3 lg:grid-cols-5">
        <Metric label="Price" value={formatNumber(price)} prefix="$" />
        <Metric
          label="Δ %"
          value={priceChangePct !== null && priceChangePct !== undefined ? priceChangePct.toFixed(2) : "--"}
          suffix="%"
        />
        <Metric label="RSI" value={formatNumber(rsi)} />
        <Metric label="Volatility" value={formatNumber(volatility)} suffix="σ" />
        <Metric
          label="Sentiment"
          value={
            sentimentScore !== undefined && sentimentScore !== null
              ? sentimentScore.toFixed(2)
              : "--"
          }
        />
        <Metric
          label="Δ Sentiment"
          value={
            sentimentDelta !== undefined && sentimentDelta !== null
              ? sentimentDelta.toFixed(2)
              : "--"
          }
        />
        <Metric label="Last updated" value={updatedDistance} />
      </div>

      {(statusMessage || rationale) && (
        <p className="mt-6 rounded-lg border border-neutral-800 bg-neutral-900/60 p-4 text-sm text-neutral-300">
          {statusMessage ?? rationale}
        </p>
      )}

      <div className="mt-4 flex items-center justify-between text-xs text-neutral-500">
        <span>Updated {updatedAt ? new Date(updatedAt).toLocaleString() : "once data is available"}</span>
        {onExplain && (
          <button
            type="button"
            onClick={() => onExplain(ticker)}
            className="rounded-full border border-neutral-700 px-3 py-1 text-xs font-medium text-neutral-200 transition hover:border-neutral-500 focus:outline-none focus:ring-2 focus:ring-coop/40"
          >
            Explain
          </button>
        )}
      </div>
    </article>
  );
}

function Metric({ label, value, prefix, suffix }: { label: string; value: string; prefix?: string; suffix?: string }) {
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-950/60 p-4">
      <p className="text-xs uppercase tracking-wide text-neutral-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-neutral-100">
        {prefix}
        {value}
        {suffix}
      </p>
    </div>
  );
}
