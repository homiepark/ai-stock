"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, Search, X } from "lucide-react";
import type { AssetClass, Verdict } from "@/lib/types";
import { cn } from "@/lib/utils";
import { LabelBadge } from "./label-badge";

type SortKey = "name" | "theme" | "short" | "mid" | "long" | "composite" | "label";
type SortDir = "asc" | "desc";

const LABEL_RANK: Record<string, number> = {
  STRONG_BUY: 5,
  ACCUMULATE: 4,
  HOLD: 3,
  TRIM: 2,
  AVOID: 1,
};

export function VerdictMatrix({
  verdicts,
  asset,
}: {
  verdicts: Verdict[];
  asset: AssetClass;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("composite");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [search, setSearch] = useState("");
  const [theme, setTheme] = useState<string | null>(null);
  const [label, setLabel] = useState<string | null>(null);
  const [country, setCountry] = useState<string | null>(null);

  const themes = useMemo(() => {
    const map = new Map<string, string>();
    verdicts.forEach((v) => {
      if (!map.has(v.theme)) map.set(v.theme, v.theme_short);
    });
    return Array.from(map.entries());
  }, [verdicts]);

  const countries = useMemo(() => {
    return Array.from(new Set(verdicts.map((v) => v.country)));
  }, [verdicts]);

  const filtered = useMemo(() => {
    return verdicts.filter((v) => {
      if (search) {
        const q = search.toLowerCase();
        const hay = `${v.name} ${v.ticker} ${v.note}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      if (theme && v.theme !== theme) return false;
      if (label && v.label !== label) return false;
      if (country && v.country !== country) return false;
      return true;
    });
  }, [verdicts, search, theme, label, country]);

  const sorted = useMemo(() => {
    const arr = [...filtered];
    arr.sort((a, b) => {
      let av: number | string;
      let bv: number | string;
      switch (sortKey) {
        case "name":
          av = a.name;
          bv = b.name;
          break;
        case "theme":
          av = a.theme_short;
          bv = b.theme_short;
          break;
        case "short":
          av = a.scores.short;
          bv = b.scores.short;
          break;
        case "mid":
          av = a.scores.mid;
          bv = b.scores.mid;
          break;
        case "long":
          av = a.scores.long;
          bv = b.scores.long;
          break;
        case "composite":
          av = a.scores.composite;
          bv = b.scores.composite;
          break;
        case "label":
          av = LABEL_RANK[a.label] ?? 0;
          bv = LABEL_RANK[b.label] ?? 0;
          break;
      }
      const sign = sortDir === "asc" ? 1 : -1;
      if (typeof av === "number" && typeof bv === "number") return (av - bv) * sign;
      return String(av).localeCompare(String(bv)) * sign;
    });
    return arr;
  }, [filtered, sortKey, sortDir]);

  function setSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir(key === "name" || key === "theme" ? "asc" : "desc");
    }
  }

  function clearFilters() {
    setSearch("");
    setTheme(null);
    setLabel(null);
    setCountry(null);
  }

  const hasFilters = !!(search || theme || label || country);

  return (
    <div className="space-y-3">
      {/* Search + filter bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="종목·티커·메모 검색..."
            className="w-full bg-slate-950 border border-slate-800 rounded-md pl-9 pr-9 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
          {search && (
            <button
              onClick={() => setSearch("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-500 hover:text-white"
              aria-label="검색 지우기"
            >
              <X className="size-4" />
            </button>
          )}
        </div>

        <div className="flex flex-wrap gap-2 text-xs">
          <FilterChips
            label="테마"
            options={themes.map(([k, v]) => ({ value: k, display: v }))}
            value={theme}
            onChange={setTheme}
          />
          <FilterChips
            label="라벨"
            options={[
              { value: "STRONG_BUY", display: "🟢 STRONG" },
              { value: "ACCUMULATE", display: "🟡 ACC" },
              { value: "HOLD", display: "⚪ HOLD" },
              { value: "TRIM", display: "🟠 TRIM" },
              { value: "AVOID", display: "🔴 AVOID" },
            ]}
            value={label}
            onChange={setLabel}
          />
          {countries.length > 1 && (
            <FilterChips
              label="국가"
              options={countries.map((c) => ({
                value: c,
                display: c === "US" ? "🇺🇸 미국" : c === "KR" ? "🇰🇷 한국" : c,
              }))}
              value={country}
              onChange={setCountry}
            />
          )}
          {hasFilters && (
            <button
              onClick={clearFilters}
              className="text-slate-400 hover:text-white px-2 py-1 rounded"
            >
              초기화
            </button>
          )}
          <span className="ml-auto text-slate-500 self-center">
            {sorted.length} / {verdicts.length}
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-950 text-slate-400 text-xs uppercase tracking-wider">
            <tr>
              <SortableTh active={sortKey === "name"} dir={sortDir} onClick={() => setSort("name")} className="text-left sticky left-0 bg-slate-950">
                종목
              </SortableTh>
              <SortableTh active={sortKey === "theme"} dir={sortDir} onClick={() => setSort("theme")} className="text-left">
                테마
              </SortableTh>
              <SortableTh active={sortKey === "short"} dir={sortDir} onClick={() => setSort("short")} className="text-right">
                단기
              </SortableTh>
              <SortableTh active={sortKey === "mid"} dir={sortDir} onClick={() => setSort("mid")} className="text-right">
                중기
              </SortableTh>
              <SortableTh active={sortKey === "long"} dir={sortDir} onClick={() => setSort("long")} className="text-right">
                장기
              </SortableTh>
              <SortableTh active={sortKey === "composite"} dir={sortDir} onClick={() => setSort("composite")} className="text-right">
                종합
              </SortableTh>
              <SortableTh active={sortKey === "label"} dir={sortDir} onClick={() => setSort("label")} className="text-center">
                라벨
              </SortableTh>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {sorted.map((v) => {
              const detailHref =
                asset === "stock" ? `/stock/${v.ticker}` : `/coin/${v.ticker}`;
              return (
                <tr key={v.ticker} className="hover:bg-slate-800/30 group">
                  <td className="px-3 py-2 sticky left-0 bg-slate-900 group-hover:bg-slate-800/30">
                    <Link href={detailHref} className="block">
                      <div className="font-medium text-white">{v.name}</div>
                      <div className="text-xs text-slate-500 font-mono">
                        {v.ticker} · {v.country}
                        {v.tier === "leader" && " ★"}
                        {v.tier === "momentum" && " ▲"}
                      </div>
                    </Link>
                  </td>
                  <td className="px-3 py-2 text-slate-400 text-xs whitespace-nowrap">
                    {v.theme_short}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-slate-300 tabular-nums">
                    {v.scores.short.toFixed(0)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-slate-300 tabular-nums">
                    {v.scores.mid.toFixed(0)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-slate-300 tabular-nums">
                    {v.scores.long.toFixed(0)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono font-semibold text-white tabular-nums">
                    {v.scores.composite.toFixed(0)}
                  </td>
                  <td className="px-3 py-2 text-center">
                    <LabelBadge label={v.label} size="sm" />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {sorted.length === 0 && (
          <div className="text-center py-12 text-slate-500 text-sm">
            조건에 맞는 종목이 없습니다.
          </div>
        )}
      </div>
    </div>
  );
}

function SortableTh({
  children,
  active,
  dir,
  onClick,
  className,
}: {
  children: React.ReactNode;
  active: boolean;
  dir: SortDir;
  onClick: () => void;
  className?: string;
}) {
  return (
    <th
      onClick={onClick}
      className={cn(
        "px-3 py-2 cursor-pointer select-none hover:bg-slate-900 whitespace-nowrap",
        active && "text-sky-400",
        className,
      )}
    >
      <span className="inline-flex items-center gap-1">
        {children}
        {active &&
          (dir === "asc" ? (
            <ArrowUp className="size-3" />
          ) : (
            <ArrowDown className="size-3" />
          ))}
      </span>
    </th>
  );
}

function FilterChips<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: Array<{ value: T; display: string }>;
  value: T | null;
  onChange: (v: T | null) => void;
}) {
  return (
    <div className="flex items-center gap-1 flex-wrap">
      <span className="text-slate-500 mr-1">{label}:</span>
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(value === opt.value ? null : opt.value)}
          className={cn(
            "px-2 py-1 rounded transition-colors",
            value === opt.value
              ? "bg-sky-600 text-white"
              : "bg-slate-800 text-slate-300 hover:bg-slate-700",
          )}
        >
          {opt.display}
        </button>
      ))}
    </div>
  );
}
