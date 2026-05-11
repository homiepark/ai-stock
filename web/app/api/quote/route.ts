// Live quote proxy — 60s CDN cache.
//
// /api/quote?kind=stock_us&symbol=NVDA
// /api/quote?kind=stock_kr&symbol=005930
// /api/quote?kind=coin&symbol=bitcoin   (CoinGecko id, not the ticker)
//
// We do this server-side so the user's browser never hits Yahoo/CoinGecko
// directly (CORS + rate limits) and so 60-second responses are shared
// across all visitors via Vercel's edge cache.
import { NextResponse } from "next/server";

export const runtime = "edge";
export const revalidate = 60;

type Quote = {
  price: number;
  change_pct: number;          // 0.0123 = +1.23%
  currency: string;            // "USD" | "KRW"
  source: "yahoo" | "coingecko";
  ts: string;                  // ISO timestamp of this server response
};

async function fetchYahoo(symbol: string): Promise<Quote> {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?range=1d&interval=1d`;
  const r = await fetch(url, {
    headers: { "User-Agent": "ai-stock/0.1" },
    next: { revalidate: 60 },
  });
  if (!r.ok) throw new Error(`yahoo ${r.status}`);
  const json = await r.json();
  const meta = json?.chart?.result?.[0]?.meta;
  if (!meta) throw new Error("yahoo: no meta");
  const price = Number(meta.regularMarketPrice);
  const prev = Number(meta.chartPreviousClose || meta.previousClose);
  if (!Number.isFinite(price) || !Number.isFinite(prev) || prev === 0) {
    throw new Error("yahoo: bad numbers");
  }
  return {
    price,
    change_pct: (price - prev) / prev,
    currency: String(meta.currency || "USD"),
    source: "yahoo",
    ts: new Date().toISOString(),
  };
}

async function fetchCoinGecko(id: string): Promise<Quote> {
  const url = `https://api.coingecko.com/api/v3/simple/price?ids=${encodeURIComponent(id)}&vs_currencies=usd&include_24hr_change=true`;
  const r = await fetch(url, {
    headers: { "User-Agent": "ai-stock/0.1" },
    next: { revalidate: 60 },
  });
  if (!r.ok) throw new Error(`coingecko ${r.status}`);
  const json = await r.json();
  const row = json?.[id];
  if (!row || typeof row.usd !== "number") {
    throw new Error("coingecko: no row");
  }
  const change_24h = Number(row.usd_24h_change ?? 0) / 100;
  return {
    price: row.usd,
    change_pct: Number.isFinite(change_24h) ? change_24h : 0,
    currency: "USD",
    source: "coingecko",
    ts: new Date().toISOString(),
  };
}

export async function GET(req: Request) {
  const u = new URL(req.url);
  const kind = u.searchParams.get("kind");
  const symbol = u.searchParams.get("symbol")?.trim();
  if (!symbol) {
    return NextResponse.json({ error: "missing symbol" }, { status: 400 });
  }

  try {
    let quote: Quote;
    if (kind === "coin") {
      quote = await fetchCoinGecko(symbol);
    } else if (kind === "stock_us") {
      quote = await fetchYahoo(symbol);
    } else if (kind === "stock_kr") {
      // Try KOSPI suffix first; fall back to KOSDAQ on 404/empty.
      try {
        quote = await fetchYahoo(`${symbol}.KS`);
      } catch {
        quote = await fetchYahoo(`${symbol}.KQ`);
      }
    } else {
      return NextResponse.json({ error: "bad kind" }, { status: 400 });
    }

    return NextResponse.json(quote, {
      headers: {
        "cache-control": "public, s-maxage=60, stale-while-revalidate=300",
      },
    });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json({ error: msg }, { status: 502 });
  }
}
