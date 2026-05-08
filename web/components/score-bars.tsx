import type { Scores } from "@/lib/types";

export function ScoreBars({ scores }: { scores: Scores }) {
  const rows: Array<{ label: string; value: number; color: string }> = [
    { label: "단기 (1~12주)", value: scores.short, color: "bg-amber-500" },
    { label: "중기 (3~12개월)", value: scores.mid, color: "bg-emerald-500" },
    { label: "장기 (1~5년)", value: scores.long, color: "bg-sky-500" },
    { label: "종합", value: scores.composite, color: "bg-violet-500" },
  ];
  return (
    <div className="space-y-3">
      {rows.map((r) => (
        <div key={r.label} className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">{r.label}</span>
            <span className="font-mono text-white tabular-nums">
              {r.value.toFixed(0)}
            </span>
          </div>
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className={`h-full ${r.color}`}
              style={{ width: `${Math.max(0, Math.min(100, r.value))}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
