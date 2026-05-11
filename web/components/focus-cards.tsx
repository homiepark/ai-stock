import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { Verdict, AssetClass } from "@/lib/types";
import { LabelBadge } from "./label-badge";

export function FocusCards({
  verdicts,
  asset,
}: {
  verdicts: Verdict[];
  asset: AssetClass;
}) {
  const focus = verdicts.filter((v) => v.in_focus).slice(0, 5);
  if (focus.length === 0) return null;

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {focus.map((f) => {
        const detailHref =
          asset === "stock" ? `/stock/${f.ticker}` : `/coin/${f.ticker}`;
        return (
          <Link
            key={f.ticker}
            href={detailHref}
            className="group bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 hover:border-slate-600 hover:bg-slate-900/80 transition-all"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="text-xs text-slate-500 mb-1">{f.theme_short}</div>
                <div className="flex items-baseline gap-2 flex-wrap">
                  <span className="font-bold text-lg text-white">{f.name}</span>
                  <span className="text-slate-500 font-mono text-sm">
                    {f.ticker}
                  </span>
                </div>
              </div>
              <LabelBadge label={f.label} size="md" />
            </div>

            {/* Score bars */}
            <div className="space-y-2">
              <ScoreLine label="단기" value={f.scores.short} />
              <ScoreLine label="중기" value={f.scores.mid} />
              <ScoreLine label="장기" value={f.scores.long} />
              <div className="pt-2 border-t border-slate-800">
                <ScoreLine
                  label="종합"
                  value={f.scores.composite}
                  highlight
                />
              </div>
            </div>

            {f.narrative.summary && (
              <p className="text-sm text-slate-300 leading-relaxed line-clamp-3">
                {f.narrative.summary}
              </p>
            )}

            <div className="space-y-1.5 text-xs">
              {f.narrative.entry_guide && (
                <div className="flex gap-2">
                  <span className="text-emerald-400 font-semibold w-12 flex-shrink-0">
                    진입
                  </span>
                  <span className="text-slate-300 line-clamp-2">
                    {f.narrative.entry_guide}
                  </span>
                </div>
              )}
              {f.narrative.risks && (
                <div className="flex gap-2">
                  <span className="text-rose-400 font-semibold w-12 flex-shrink-0">
                    리스크
                  </span>
                  <span className="text-slate-300 line-clamp-2">
                    {f.narrative.risks}
                  </span>
                </div>
              )}
              {f.narrative.next_trigger && (
                <div className="flex gap-2">
                  <span className="text-sky-400 font-semibold w-12 flex-shrink-0">
                    트리거
                  </span>
                  <span className="text-slate-300 line-clamp-2">
                    {f.narrative.next_trigger}
                  </span>
                </div>
              )}
            </div>

            <div className="flex items-center justify-end text-xs text-slate-500 group-hover:text-sky-400 transition-colors">
              상세 보기 <ArrowRight className="size-3 ml-1" />
            </div>
          </Link>
        );
      })}
    </div>
  );
}

function ScoreLine({
  label,
  value,
  highlight,
}: {
  label: string;
  value: number;
  highlight?: boolean;
}) {
  const pct = Math.max(0, Math.min(100, value));
  const color =
    value >= 70
      ? "bg-emerald-500"
      : value >= 55
        ? "bg-lime-500"
        : value >= 45
          ? "bg-slate-500"
          : value >= 30
            ? "bg-amber-500"
            : "bg-rose-500";

  return (
    <div className="flex items-center gap-3 text-xs">
      <span
        className={`w-8 flex-shrink-0 ${
          highlight ? "text-sky-300 font-semibold" : "text-slate-400"
        }`}
      >
        {label}
      </span>
      <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span
        className={`w-8 text-right font-mono tabular-nums ${
          highlight ? "text-sky-300 font-semibold" : "text-white"
        }`}
      >
        {value.toFixed(0)}
      </span>
    </div>
  );
}
