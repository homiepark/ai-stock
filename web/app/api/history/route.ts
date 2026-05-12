// Daily OHLCV history proxy — 1-hour edge cache.
//
// /api/history?kind=stock_us&symbol=NVDA
// /api/history?kind=stock_kr&symbol=005930
// /api/history?kind=coin&symbol=bitcoin   (CoinGecko id)
//
// Returns the last ~180 daily bars in lightweight-charts time-series
// format. We cache 1 hour because daily bars don't change intraday
// (and the dashboard's overall page already revalidates hourly).
import { NextResponse } from "next/server";

export const runtime = "edge";
export const revalidate = 3600;

type Bar = {
  time: number;       // unix seconds
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

async function yahooHistory(symbol: string): Promise<Bar[]> {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?range=6mo&interval=1d`;
  const r = await fetch(url, {
    headers: { "User-Agent": "ai-stock/0.1" },
    next: { revalidate: 3600 },
  });
  if (!r.ok) throw new Error(`yahoo ${r.status}`);
  const json = await r.json();
  const result = json?.chart?.result?.[0];
  if (!result) throw new Error("yahoo: no result");
  const ts: number[] = result.timestamp || [];
  const q = result.indicators?.quote?.[0] || {};
  const bars: Bar[] = [];
  for (let i = 0; i < ts.length; i++) {
    const o = q.open?.[i];
    const h = q.high?.[i];
    const l = q.low?.[i];
    const c = q.close?.[i];
    const v = q.volume?.[i];
    if (
      typeof o !== "number" || typeof h !== "number" ||
      typeof l !== "number" || typeof c !== "number"
    ) continue;
    bars.push({ time: ts[i], open: o, high: h, low: l, close: c, volume: v || 0 });
  }
  return bars;
}

async function coingeckoHistory(id: string): Promise<Bar[]> {
  // /coins/{id}/ohlc gives 4h candles, but only over a limited range.
  // We piece together daily OHLC from /coins/{id}/market_chart instead
  // (prices + volumes by day; CoinGecko free tier returns daily resolution
  // when days >= 90).
  const url = `https://api.coingecko.com/api/v3/coins/${encodeURIComponent(id)}/market_chart?vs_currency=usd&days=180&interval=daily`;
  const r = await fetch(url, {
    headers: { "User-Agent": "ai-stock/0.1" },
    next: { revalidate: 3600 },
  });
  if (!r.ok) throw new Error(`coingecko ${r.status}`);
  const json = await r.json();
  const prices: [number, number][] = json?.prices || [];
  const volumes: [number, number][] = json?.total_volumes || [];
  if (!prices.length) throw new Error("coingecko: empty");

  const volMap = new Map<number, number>();
  for (const [ms, v] of volumes) volMap.set(Math.floor(ms / 86400_000), v);

  const bars: Bar[] = [];
  let prevClose = prices[0][1];
  for (const [ms, p] of prices) {
    const day = Math.floor(ms / 86400_000);
    const open = prevClose;
    const close = p;
    const high = Math.max(open, close);
    const low = Math.min(open, close);
    bars.push({
      time: day * 86400,
      open, high, low, close,
      volume: volMap.get(day) || 0,
    });
    prevClose = close;
  }
  return bars;
}

export async function GET(req: Request) {
  const u = new URL(req.url);
  const kind = u.searchParams.get("kind");
  const symbol = u.searchParams.get("symbol")?.trim();
  if (!symbol) {
    return NextResponse.json({ error: "missing symbol" }, { status: 400 });
  }

  try {
    let bars: Bar[];
    if (kind === "coin") {
      bars = await coingeckoHistory(symbol);
    } else if (kind === "stock_us") {
      bars = await yahooHistory(symbol);
    } else if (kind === "stock_kr") {
      try {
        bars = await yahooHistory(`${symbol}.KS`);
      } catch {
        bars = await yahooHistory(`${symbol}.KQ`);
      }
    } else {
      return NextResponse.json({ error: "bad kind" }, { status: 400 });
    }
    return NextResponse.json(
      { bars },
      {
        headers: {
          "cache-control": "public, s-maxage=3600, stale-while-revalidate=86400",
        },
      },
    );
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json({ error: msg }, { status: 502 });
  }
}
