import { numFmt, pctFmt, changeColor } from "@/lib/utils";

export function MetricsGrid({
  metrics,
}: {
  metrics: Record<string, number | null>;
}) {
  if (!metrics || Object.keys(metrics).length === 0) return null;

  const rows: Array<{ label: string; value: number | null; format?: "pct" | "num" }> = [
    { label: "종가", value: metrics.last_close, format: "num" },
    { label: "RSI(14)", value: metrics.rsi14, format: "num" },
    { label: "50일 이평", value: metrics.ma50, format: "num" },
    { label: "200일 이평", value: metrics.ma200, format: "num" },
    { label: "5일 수익률", value: metrics.ret_5d, format: "pct" },
    { label: "20일 수익률", value: metrics.ret_20d, format: "pct" },
    { label: "60일 수익률", value: metrics.ret_60d, format: "pct" },
    { label: "거래량 Z(20)", value: metrics.vol_z20, format: "num" },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
      {rows.map((r) => (
        <div
          key={r.label}
          className="bg-slate-900 border border-slate-800 rounded-lg p-3"
        >
          <div className="text-xs text-slate-400 truncate">{r.label}</div>
          <div
            className={`text-base font-mono font-semibold tabular-nums ${
              r.format === "pct" && r.value !== null
                ? changeColor(r.value)
                : "text-white"
            }`}
          >
            {r.value === null || r.value === undefined
              ? "—"
              : r.format === "pct"
                ? pctFmt(r.value, 1)
                : numFmt(r.value)}
          </div>
        </div>
      ))}
    </div>
  );
}
