// Wire types — must match src/ai_stock/report/json_export.py

export type LabelText = "STRONG_BUY" | "ACCUMULATE" | "HOLD" | "TRIM" | "AVOID";

export type AssetClass = "stock" | "coin";

export interface Scores {
  short: number;
  mid: number;
  long: number;
  composite: number;
}

export interface Narrative {
  summary: string;
  entry_guide: string;
  risks: string;
  next_trigger: string;
}

export interface Overheat {
  score: number;
  level: "normal" | "mild" | "high" | "extreme";
  emoji: string;
  label: string;
  guidance: string;
  flags: string[];
}

export interface Verdict {
  ticker: string;
  name: string;
  country: string;
  tier: "leader" | "momentum" | "supporting" | string;
  theme: string;
  theme_short: string;
  note: string;
  coingecko_id: string;
  scores: Scores;
  label: LabelText;
  label_quant: LabelText;
  narrative: Narrative;
  metrics: Record<string, number | null>;
  overheat: Overheat | null;
  in_focus: boolean;
}

export interface ThemeRanking {
  theme_key: string;
  theme_name: string;
  composite_return: number;
  avg_return_1w: number;
  avg_return_1m: number;
  avg_return_3m: number;
  cap_leader: { ticker: string; name: string } | null;
  momentum_leader: { ticker: string; name: string } | null;
  member_count: number;
  tagline?: string;
  why_now?: string;
  risk?: string;
}

export interface MacroSnapshot {
  [key: string]: { name: string; value: number; change: number };
}

export interface NewsItem {
  title: string;
  link: string;
  summary: string;
  published: string;
  source: string;
  matched_tickers: string[];
  matched_names: string[];
}

export interface LabelChange {
  ticker: string;
  name: string;
  old_label: LabelText;
  new_label: LabelText;
}

export interface SocialPulse {
  trending: Array<{
    ticker: string;
    name: string;
    rank: number;
    rank_24h_ago: number;
    mentions: number;
    mentions_24h_ago: number;
    delta_pct: number;
    is_rising: boolean;
  }>;
  influencer_count: number;
  influencer_categories: Record<
    string,
    Array<{ handle: string; name: string; weight: number; note: string }>
  >;
  tweet_samples: Array<{
    handle: string;
    name?: string;
    text: string;
    ts: string;
    link: string;
    likes?: number;
    retweets?: number;
    score?: number | null;
    weight?: number;
  }>;
  source_status: {
    sorsa?: string;
    apewisdom: string;
    twitter_rss: string;
  };
}

export interface DailyContext {
  asset_class: AssetClass;
  date: string;
  generated_at: string;
  version: string;
  universe_size: number;
  us_count: number;
  kr_count: number;
  macro: MacroSnapshot;
  theme_rankings: ThemeRanking[];
  verdicts: Verdict[];
  focus_tickers: string[];
  top_news: NewsItem[];
  label_changes: LabelChange[];
  social: SocialPulse | null;
}

export interface Manifest {
  stock: string[];
  coin: string[];
}
