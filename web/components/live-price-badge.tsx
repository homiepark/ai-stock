"use client";

import { useEffect, useState } from "react";

interface Props {
  /** Yahoo ticker for stocks, CoinGecko id for coins. */
  symbol: string;
  kind: "stock_us" | "stock_kr" | "coin";
  /** Polling interval. Default 60s — server already caches 60s, so don't go below. */
  intervalMs?: number;
}

type Quote = {
  price: number;
  change_pct: number;
  currency: string;
  source: "yahoo" | "coingecko";
  ts: string;
};

function fmtPrice(p: number, currency: string): string {
  if (currency === "KRW") return `₩${Math.round(p).toLocaleString()}`;
  if (p >= 1000) return `$${p.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
  if (p >= 1) return `$${p.toFixed(2)}`;
  return `$${p.toFixed(4)}`;
}

function fmtPct(c: number): string {
  const v = (c * 100).toFixed(2);
  return c > 0 ? `+${v}%` : `${v}%`;
}

export function LivePriceBadge({ symbol, kind, intervalMs = 60_000 }: Props) {
  const [quote, setQuote] = useState<Quote | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      try {
        const r = await fetch(
          `/api/quote?kind=${kind}&symbol=${encodeURIComponent(symbol)}`,
          { cache: "no-store" },
        );
        if (!r.ok) throw new Error(`${r.status}`);
        const data = await r.json();
        if (!cancelled) {
          setQuote(data);
          setErr(null);
        }
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "fetch failed");
      }
    }
    run();
    const id = setInterval(run, intervalMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [symbol, kind, intervalMs]);

  if (err && !quote) {
    return (
      <span className="text-xs text-slate-500" title={err}>
        Live —
      </span>
    );
  }
  if (!quote) {
    return <span className="text-xs text-slate-500">Live …</span>;
  }
  const positive = quote.change_pct > 0;
  const negative = quote.change_pct < 0;
  const color = positive
    ? "text-emerald-400"
    : negative
    ? "text-rose-400"
    : "text-slate-300";
  return (
    <span
      className="inline-flex items-baseline gap-1.5 text-sm font-mono tabular-nums"
      title={`마지막 갱신: ${new Date(quote.ts).toLocaleTimeString()} · 60초 캐시`}
    >
      <span className="text-[0.65rem] uppercase tracking-wider text-slate-500">
        Live
      </span>
      <span className="text-white">{fmtPrice(quote.price, quote.currency)}</span>
      <span className={color}>{fmtPct(quote.change_pct)}</span>
    </span>
  );
}
