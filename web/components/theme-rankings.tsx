import type { ThemeRanking } from "@/lib/types";
import { changeColor, pctFmt } from "@/lib/utils";

export function ThemeRankings({ rankings }: { rankings: ThemeRanking[] }) {
  if (!rankings || rankings.length === 0) return null;
  const maxAbs =
    Math.max(...rankings.map((r) => Math.abs(r.composite_return)), 0.0001) || 0.0001;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
      {rankings.map((r, idx) => {
        const pct = (r.composite_return / maxAbs) * 50;
        return (
          <div
            key={r.theme_key}
            className={`px-4 py-3 ${
              idx < rankings.length - 1 ? "border-b border-slate-800" : ""
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-xs text-slate-500 font-mono">#{idx + 1}</span>
                <span className="font-medium text-white truncate">{r.theme_name}</span>
              </div>
              <div
                className={`text-sm font-mono tabular-nums flex-shrink-0 ml-2 ${changeColor(
                  r.composite_return,
                )}`}
              >
                {pctFmt(r.composite_return)}
              </div>
            </div>
            <div className="relative h-1.5 bg-slate-800 rounded-full overflow-hidden">
              {r.composite_return >= 0 ? (
                <div
                  className="absolute left-1/2 top-0 bottom-0 bg-emerald-500"
                  style={{ width: `${pct}%` }}
                />
              ) : (
                <div
                  className="absolute right-1/2 top-0 bottom-0 bg-rose-500"
                  style={{ width: `${-pct}%` }}
                />
              )}
              <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-600" />
            </div>
            <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
              <span>
                1주{" "}
                <span className={`font-mono tabular-nums ${changeColor(r.avg_return_1w)}`}>
                  {pctFmt(r.avg_return_1w, 1)}
                </span>
              </span>
              <span>
                1개월{" "}
                <span className={`font-mono tabular-nums ${changeColor(r.avg_return_1m)}`}>
                  {pctFmt(r.avg_return_1m, 1)}
                </span>
              </span>
              <span>
                3개월{" "}
                <span className={`font-mono tabular-nums ${changeColor(r.avg_return_3m)}`}>
                  {pctFmt(r.avg_return_3m, 1)}
                </span>
              </span>
              {r.cap_leader && (
                <span>
                  시총: <span className="text-slate-200">{r.cap_leader.name}</span>
                </span>
              )}
              {r.momentum_leader &&
                r.momentum_leader.ticker !== (r.cap_leader?.ticker || "") && (
                  <span>
                    모멘텀:{" "}
                    <span className="text-sky-400">{r.momentum_leader.name}</span>
                  </span>
                )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
