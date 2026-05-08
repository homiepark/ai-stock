import Link from "next/link";
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
            className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3 hover:border-slate-700 transition-colors"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <div className="text-xs text-slate-500 mb-0.5">{f.theme_short}</div>
                <div className="font-semibold text-white truncate">
                  {f.name}{" "}
                  <span className="text-slate-500 font-mono text-sm">{f.ticker}</span>
                </div>
              </div>
              <LabelBadge label={f.label} />
            </div>

            <div className="grid grid-cols-4 gap-2 text-center">
              <ScoreCell label="단기" value={f.scores.short} />
              <ScoreCell label="중기" value={f.scores.mid} />
              <ScoreCell label="장기" value={f.scores.long} />
              <ScoreCell
                label="종합"
                value={f.scores.composite}
                highlight
              />
            </div>

            {f.narrative.summary && (
              <p className="text-sm text-slate-300 leading-relaxed line-clamp-3">
                {f.narrative.summary}
              </p>
            )}

            <div className="space-y-1 text-xs">
              {f.narrative.entry_guide && (
                <div>
                  <span className="text-emerald-400 font-medium">진입</span>{" "}
                  <span className="text-slate-300">{f.narrative.entry_guide}</span>
                </div>
              )}
              {f.narrative.risks && (
                <div>
                  <span className="text-rose-400 font-medium">리스크</span>{" "}
                  <span className="text-slate-300">{f.narrative.risks}</span>
                </div>
              )}
              {f.narrative.next_trigger && (
                <div>
                  <span className="text-sky-400 font-medium">트리거</span>{" "}
                  <span className="text-slate-300">{f.narrative.next_trigger}</span>
                </div>
              )}
            </div>
          </Link>
        );
      })}
    </div>
  );
}

function ScoreCell({
  label,
  value,
  highlight,
}: {
  label: string;
  value: number;
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded p-2 ${
        highlight ? "bg-sky-950 ring-1 ring-sky-800" : "bg-slate-950"
      }`}
    >
      <div className={`text-xs ${highlight ? "text-sky-300" : "text-slate-500"}`}>
        {label}
      </div>
      <div
        className={`font-mono text-sm tabular-nums ${
          highlight ? "font-semibold text-sky-300" : "text-white"
        }`}
      >
        {value.toFixed(0)}
      </div>
    </div>
  );
}
