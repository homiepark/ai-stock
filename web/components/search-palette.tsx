"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, TrendingUp } from "lucide-react";
import type { AssetClass, ThemeRanking, Verdict } from "@/lib/types";
import { LabelBadge } from "./label-badge";

export function SearchPalette({
  verdicts,
  themeRankings,
  asset,
}: {
  verdicts: Verdict[];
  themeRankings: ThemeRanking[];
  asset: AssetClass;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  // Open on Cmd/Ctrl+K and on global event
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === "Escape") setOpen(false);
    }
    function onOpen() {
      setOpen(true);
    }
    window.addEventListener("keydown", onKey);
    window.addEventListener("ai-stock:open-search", onOpen as EventListener);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("ai-stock:open-search", onOpen as EventListener);
    };
  }, []);

  useEffect(() => {
    if (open) {
      setQuery("");
      setActive(0);
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    type R =
      | { kind: "verdict"; v: Verdict }
      | { kind: "theme"; t: ThemeRanking };
    const out: R[] = [];

    if (!q) {
      // Show focus stocks + top themes
      verdicts
        .filter((v) => v.in_focus)
        .slice(0, 5)
        .forEach((v) => out.push({ kind: "verdict", v }));
      themeRankings.slice(0, 3).forEach((t) => out.push({ kind: "theme", t }));
      return out;
    }

    verdicts.forEach((v) => {
      const hay = `${v.name} ${v.ticker} ${v.theme_short} ${v.note}`.toLowerCase();
      if (hay.includes(q)) out.push({ kind: "verdict", v });
    });
    themeRankings.forEach((t) => {
      if (t.theme_name.toLowerCase().includes(q)) out.push({ kind: "theme", t });
    });
    return out.slice(0, 30);
  }, [query, verdicts, themeRankings]);

  function navigate(idx: number) {
    const r = results[idx];
    if (!r) return;
    if (r.kind === "verdict") {
      const path = asset === "stock" ? `/stock/${r.v.ticker}` : `/coin/${r.v.ticker}`;
      router.push(path);
    } else {
      router.push(`/?theme=${r.t.theme_key}`);
    }
    setOpen(false);
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      navigate(active);
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-start justify-center pt-[15vh] px-4"
      onClick={() => setOpen(false)}
    >
      <div
        className="bg-slate-900 border border-slate-800 rounded-lg shadow-2xl w-full max-w-xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="border-b border-slate-800 px-4 py-3 flex items-center gap-3">
          <Search className="size-4 text-slate-500 flex-shrink-0" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActive(0);
            }}
            onKeyDown={onKeyDown}
            placeholder="종목·티커·테마 검색..."
            className="flex-1 bg-transparent outline-none text-sm text-white placeholder:text-slate-500"
          />
          <kbd className="text-xs text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
            ESC
          </kbd>
        </div>
        <div className="max-h-[50vh] overflow-y-auto">
          {results.length === 0 && (
            <div className="px-4 py-8 text-center text-slate-500 text-sm">
              결과 없음
            </div>
          )}
          {results.map((r, i) => {
            const isActive = i === active;
            const cls = `px-4 py-2.5 flex items-center gap-3 cursor-pointer ${
              isActive ? "bg-slate-800" : "hover:bg-slate-800/50"
            }`;
            if (r.kind === "verdict") {
              return (
                <button
                  key={`v-${r.v.ticker}`}
                  className={`${cls} w-full text-left`}
                  onMouseEnter={() => setActive(i)}
                  onClick={() => navigate(i)}
                >
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-white truncate">
                      <span className="font-medium">{r.v.name}</span>{" "}
                      <span className="text-slate-500 font-mono text-xs">
                        {r.v.ticker}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 truncate">
                      {r.v.theme_short} · {r.v.country}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="text-xs font-mono text-slate-300 tabular-nums">
                      {r.v.scores.composite.toFixed(0)}
                    </span>
                    <LabelBadge label={r.v.label} size="sm" />
                  </div>
                </button>
              );
            }
            return (
              <button
                key={`t-${r.t.theme_key}`}
                className={`${cls} w-full text-left`}
                onMouseEnter={() => setActive(i)}
                onClick={() => navigate(i)}
              >
                <TrendingUp className="size-4 text-slate-500" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-white truncate">{r.t.theme_name}</div>
                  <div className="text-xs text-slate-500">
                    {r.t.member_count}종목
                  </div>
                </div>
              </button>
            );
          })}
        </div>
        <div className="border-t border-slate-800 px-4 py-2 text-xs text-slate-500 flex items-center justify-between">
          <span>
            <kbd className="bg-slate-800 px-1 rounded">↑↓</kbd> 이동{" "}
            <kbd className="bg-slate-800 px-1 rounded ml-1">↵</kbd> 선택
          </span>
          <span>
            <kbd className="bg-slate-800 px-1 rounded">⌘K</kbd> 토글
          </span>
        </div>
      </div>
    </div>
  );
}
