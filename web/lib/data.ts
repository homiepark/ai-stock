// Data loaders. JSON lives at ./data/ and is read at build time (server components).
// Files are gitignored locally but committed by GitHub Actions on every daily run.

import fs from "node:fs/promises";
import path from "node:path";
import type { AssetClass, DailyContext, Manifest } from "./types";

const DATA_DIR = path.join(process.cwd(), "data");

// Empty fallback so dev mode works before the first Python build runs
const EMPTY_CONTEXT = (asset: AssetClass): DailyContext => ({
  asset_class: asset,
  date: new Date().toISOString().slice(0, 10),
  generated_at: new Date().toISOString(),
  version: "0.0.0",
  universe_size: 0,
  us_count: 0,
  kr_count: 0,
  macro: {},
  theme_rankings: [],
  verdicts: [],
  focus_tickers: [],
  top_news: [],
  label_changes: [],
  social: null,
});

async function readJson<T>(filePath: string): Promise<T | null> {
  try {
    const buf = await fs.readFile(filePath, "utf-8");
    return JSON.parse(buf) as T;
  } catch {
    return null;
  }
}

export async function loadLatest(asset: AssetClass): Promise<DailyContext> {
  const p = path.join(DATA_DIR, `latest-${asset}.json`);
  const ctx = await readJson<DailyContext>(p);
  return ctx ?? EMPTY_CONTEXT(asset);
}

export async function loadByDate(
  asset: AssetClass,
  date: string,
): Promise<DailyContext | null> {
  const p = path.join(DATA_DIR, asset, `${date}.json`);
  return readJson<DailyContext>(p);
}

export async function loadManifest(): Promise<Manifest> {
  const m = await readJson<Manifest>(path.join(DATA_DIR, "index.json"));
  return m ?? { stock: [], coin: [] };
}

// Helpers for client-side filtering ----------------------------------------

export function filterVerdicts(
  verdicts: DailyContext["verdicts"],
  filters: {
    search?: string;
    theme?: string | null;
    label?: string | null;
    country?: string | null;
    minComposite?: number;
  },
) {
  return verdicts.filter((v) => {
    if (filters.search) {
      const q = filters.search.toLowerCase();
      const hay = `${v.name} ${v.ticker} ${v.note} ${v.theme_short}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    if (filters.theme && v.theme !== filters.theme) return false;
    if (filters.label && v.label !== filters.label) return false;
    if (filters.country && v.country !== filters.country) return false;
    if (filters.minComposite !== undefined && v.scores.composite < filters.minComposite)
      return false;
    return true;
  });
}
