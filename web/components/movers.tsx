import Link from "next/link";
import { TrendingUp, TrendingDown } from "lucide-react";
import type { AssetClass, Verdict } from "@/lib/types";
import { changeColor, pctFmt } from "@/lib/utils";

export function Movers({
  verdicts,
  asset,
}: {
  verdicts: Verdict[];
  asset: AssetClass;
}) {
  const withReturns = verdicts
    .filter((v) => v.metrics?.ret_60d !== null && v.metrics?.ret_60d !== undefined)
    .map((v) => ({ v, ret: v.metrics.ret_60d as number }));

  if (withReturns.length === 0) return null;

  const sorted = [...withReturns].sort((a, b) => b.ret - a.ret);
  const gainers = sorted.slice(0, 5);
  const losers = sorted.slice(-5).reverse();

  const detailHref = (t: string) =>
    asset === "stock" ? `/stock/${t}` : `/coin/${t}`;

  return (
    <section>
      <h2 className="text-lg font-semibold text-white mb-3">
        🚦 빅무버 — 최근 60일 수익률
      </h2>
      <div className="grid sm:grid-cols-2 gap-3">
        <MoverList
          icon={<TrendingUp className="size-4 text-emerald-400" />}
          title="상위 5"
          items={gainers}
          detailHref={detailHref}
        />
        <MoverList
          icon={<TrendingDown className="size-4 text-rose-400" />}
          title="하위 5"
          items={losers}
          detailHref={detailHref}
        />
      </div>
    </section>
  );
}

function MoverList({
  icon,
  title,
  items,
  detailHref,
}: {
  icon: React.ReactNode;
  title: string;
  items: Array<{ v: Verdict; ret: number }>;
  detailHref: (t: string) => string;
}) {
  const maxAbs = Math.max(...items.map((i) => Math.abs(i.ret)), 0.0001);
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
      <div className="px-4 py-2 bg-slate-950 text-xs text-slate-400 uppercase tracking-wider flex items-center gap-2">
        {icon} {title}
      </div>
      <div className="divide-y divide-slate-800">
        {items.map(({ v, ret }) => {
          const pct = (Math.abs(ret) / maxAbs) * 100;
          return (
            <Link
              key={v.ticker}
              href={detailHref(v.ticker)}
              className="block px-4 py-2.5 hover:bg-slate-800/50 relative"
            >
              <div
                className={`absolute inset-y-0 left-0 ${
                  ret >= 0 ? "bg-emerald-500/10" : "bg-rose-500/10"
                }`}
                style={{ width: `${pct}%` }}
              />
              <div className="relative flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-sm text-white font-medium truncate">
                    {v.name}
                  </div>
                  <div className="text-[11px] text-slate-500 font-mono">
                    {v.ticker} · {v.theme_short}
                  </div>
                </div>
                <div
                  className={`text-sm font-mono font-semibold tabular-nums ${changeColor(
                    ret,
                  )}`}
                >
                  {pctFmt(ret, 1)}
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
