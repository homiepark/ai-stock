"use client";

import { useMemo, useState } from "react";
import type { NewsItem } from "@/lib/types";

interface Props {
  news: NewsItem[];
  /** Theme key → short display label (e.g. "semiconductors" → "반도체"). */
  themes?: { key: string; label: string }[];
}

export function NewsList({ news, themes = [] }: Props) {
  const [activeTheme, setActiveTheme] = useState<string | null>(null);

  // Per-theme counts based on what's actually in the news list, so chips
  // for empty themes never appear.
  const themeCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const n of news) {
      for (const t of n.matched_themes || []) {
        counts.set(t, (counts.get(t) || 0) + 1);
      }
    }
    return counts;
  }, [news]);

  const visibleThemes = themes.filter((t) => (themeCounts.get(t.key) || 0) > 0);

  const filtered = activeTheme
    ? news.filter((n) => (n.matched_themes || []).includes(activeTheme))
    : news;

  if (!news || news.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 text-center text-slate-500 text-sm">
        워치리스트 종목 관련 뉴스 없음
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {visibleThemes.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          <button
            onClick={() => setActiveTheme(null)}
            className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
              activeTheme === null
                ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                : "bg-slate-800 text-slate-400 hover:bg-slate-700 border border-transparent"
            }`}
          >
            전체 ({news.length})
          </button>
          {visibleThemes.map((t) => {
            const count = themeCounts.get(t.key) || 0;
            const active = activeTheme === t.key;
            return (
              <button
                key={t.key}
                onClick={() => setActiveTheme(active ? null : t.key)}
                className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                  active
                    ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                    : "bg-slate-800 text-slate-400 hover:bg-slate-700 border border-transparent"
                }`}
              >
                {t.label} ({count})
              </button>
            );
          })}
        </div>
      )}
      <div className="bg-slate-900 border border-slate-800 rounded-lg divide-y divide-slate-800">
        {filtered.length === 0 ? (
          <div className="p-6 text-center text-slate-500 text-sm">
            이 테마의 뉴스 없음
          </div>
        ) : (
          filtered.map((n, i) => (
            <a
              key={i}
              href={n.link}
              target="_blank"
              rel="noopener"
              className="block px-4 py-3 hover:bg-slate-800/50 transition-colors"
            >
              <div className="text-sm text-white">{n.title}</div>
              <div className="mt-1 flex flex-wrap gap-1.5 text-xs">
                {n.matched_names?.slice(0, 3).map((name, j) => (
                  <span
                    key={j}
                    className="px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded"
                  >
                    {name}
                  </span>
                ))}
                <span className="text-slate-500 ml-auto">{n.source}</span>
              </div>
            </a>
          ))
        )}
      </div>
    </div>
  );
}
