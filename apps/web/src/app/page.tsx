import Link from "next/link";

const seededAssets = [
  { ticker: "NVDA", name: "NVIDIA Corporation" },
  { ticker: "BTC-USD", name: "Bitcoin" }
];

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-8 px-6 py-12">
      <section className="rounded-2xl border border-neutral-700 bg-neutral-900/60 p-8 shadow-xl backdrop-blur">
        <div className="flex flex-col gap-2">
          <span className="text-sm uppercase tracking-wide text-neutral-400">
            Sprint 1
          </span>
          <h1 className="text-4xl font-semibold">
            Tit-for-Tat Asset Tracker MVP
          </h1>
          <p className="text-neutral-300">
            Foundations for an iterated game theory dashboard: backend ingest,
            indicators, API contracts, and frontend scaffolding.
          </p>
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <article className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-6">
          <h2 className="text-xl font-semibold text-neutral-100">
            Quick Links
          </h2>
          <ul className="mt-4 space-y-3 text-neutral-300">
            <li>
              <Link href="http://localhost:8000/docs" className="hover:text-white">
                Backend OpenAPI Docs
              </Link>
            </li>
            <li>
              <Link href="https://github.com/zacharythomas" className="hover:text-white">
                Project GitHub Workspace
              </Link>
            </li>
          </ul>
          <div className="mt-4 rounded-lg border border-neutral-800 bg-neutral-900 p-4 text-sm text-neutral-300">
            Trigger ingest via
            <code className="ml-2 rounded bg-neutral-800 px-2 py-1 font-mono text-xs text-neutral-100">
              curl -X POST http://localhost:8000/ingest/run
            </code>
          </div>
        </article>

        <article className="rounded-xl border border-neutral-800 bg-neutral-900/70 p-6">
          <h2 className="text-xl font-semibold text-neutral-100">
            Seed Assets
          </h2>
          <p className="mt-2 text-neutral-300">
            Preloaded assets for validating ingestion, indicator calculation, and
            API responses.
          </p>
          <ul className="mt-4 space-y-2">
            {seededAssets.map((asset) => (
              <li
                key={asset.ticker}
                className="flex items-center justify-between rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-3 text-neutral-200"
              >
                <span className="font-mono text-lg">{asset.ticker}</span>
                <span className="text-sm text-neutral-400">{asset.name}</span>
              </li>
            ))}
          </ul>
        </article>
      </section>
    </main>
  );
}
