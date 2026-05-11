import type { BacktestSummary } from "@/lib/types";

interface Props {
  summary?: BacktestSummary | null;
}

const LABEL_ORDER = ["STRONG_BUY", "ACCUMULATE", "HOLD", "TRIM", "AVOID"] as const;
const LABEL_COLOR: Record<string, string> = {
  STRONG_BUY: "text-emerald-400",
  ACCUMULATE: "text-yellow-400",
  HOLD: "text-slate-300",
  TRIM: "text-orange-400",
  AVOID: "text-rose-400",
};

const OVERHEAT_ORDER = ["normal", "mild", "high", "extreme"] as const;
const OVERHEAT_COLOR: Record<string, string> = {
  normal: "text-emerald-400",
  mild: "text-yellow-400",
  high: "text-orange-400",
  extreme: "text-rose-400",
};
const OVERHEAT_LABEL: Record<string, string> = {
  normal: "🟢 정상",
  mild: "🟡 약과열",
  high: "🟠 과열",
  extreme: "🔴 극과열",
};

function pct(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const x = (v * 100).toFixed(2);
  return v > 0 ? `+${x}%` : `${x}%`;
}

function pctColor(v: number | null | undefined): string {
  if (v === null || v === undefined) return "text-slate-500";
  return v > 0 ? "text-emerald-400" : v < 0 ? "text-rose-400" : "text-slate-300";
}

export function BacktestSummary({ summary }: Props) {
  if (!summary || summary.n_records === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 text-sm text-slate-500">
        <div className="font-medium text-white mb-1">📊 시그널 검증</div>
        데이터 누적 중. 첫 의미있는 통계는 발행 시점 + 5거래일 후부터 채워집니다.
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-white">
          📊 시그널 검증{" "}
          <span className="text-xs font-normal text-slate-500">
            — 라벨 발행 후 평균 forward return
          </span>
        </h3>
        <div className="text-xs text-slate-500 mt-1">
          누적 라벨 {summary.n_records.toLocaleString()}건 · 5d 채워짐{" "}
          {summary.n_with_5d.toLocaleString()} / 20d {summary.n_with_20d.toLocaleString()} /
          60d {summary.n_with_60d.toLocaleString()}
        </div>
      </div>

      <table className="w-full text-xs">
        <thead>
          <tr className="text-slate-500 border-b border-slate-800">
            <th className="text-left py-1.5 font-normal">라벨</th>
            <th className="text-right py-1.5 font-normal">5일 평균</th>
            <th className="text-right py-1.5 font-normal">20일 평균</th>
            <th className="text-right py-1.5 font-normal">60일 평균</th>
          </tr>
        </thead>
        <tbody>
          {LABEL_ORDER.map((label) => {
            const b = summary.by_label[label];
            if (!b) return null;
            return (
              <tr key={label} className="border-b border-slate-800/60 last:border-0">
                <td className={`py-1.5 font-medium ${LABEL_COLOR[label] || ""}`}>
                  {label}
                </td>
                {(["return_5d", "return_20d", "return_60d"] as const).map((win) => {
                  const cell = b[win];
                  return (
                    <td
                      key={win}
                      className={`py-1.5 text-right font-mono tabular-nums ${pctColor(
                        cell?.mean,
                      )}`}
                    >
                      {pct(cell?.mean)}
                      <span className="text-[0.6rem] text-slate-500 ml-1">
                        n={cell?.n ?? 0}
                      </span>
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>

      <details className="text-xs">
        <summary className="cursor-pointer text-slate-400 hover:text-white">
          과열도별 / 시그널 IC 보기
        </summary>
        <div className="mt-3 space-y-3">
          <div>
            <div className="text-slate-500 mb-1">과열도별 forward return</div>
            <table className="w-full">
              <tbody>
                {OVERHEAT_ORDER.map((lv) => {
                  const b = summary.by_overheat[lv];
                  if (!b) return null;
                  return (
                    <tr key={lv} className="border-b border-slate-800/60">
                      <td className={`py-1 ${OVERHEAT_COLOR[lv] || ""}`}>
                        {OVERHEAT_LABEL[lv] || lv}
                      </td>
                      {(["return_5d", "return_20d", "return_60d"] as const).map((win) => {
                        const cell = b[win];
                        return (
                          <td
                            key={win}
                            className={`py-1 text-right font-mono tabular-nums ${pctColor(
                              cell?.mean,
                            )}`}
                          >
                            {pct(cell?.mean)}
                            <span className="text-[0.6rem] text-slate-500 ml-1">
                              n={cell?.n ?? 0}
                            </span>
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div>
            <div className="text-slate-500 mb-1">
              Signal IC{" "}
              <span className="text-slate-600">
                (Spearman corr: composite_score vs forward return, |IC| ≥ 0.05면 alpha 있음)
              </span>
            </div>
            <div className="flex gap-4 font-mono tabular-nums">
              <span>
                5d:{" "}
                <span className={pctColor(summary.signal_ic.return_5d)}>
                  {summary.signal_ic.return_5d?.toFixed(3) ?? "—"}
                </span>
              </span>
              <span>
                20d:{" "}
                <span className={pctColor(summary.signal_ic.return_20d)}>
                  {summary.signal_ic.return_20d?.toFixed(3) ?? "—"}
                </span>
              </span>
              <span>
                60d:{" "}
                <span className={pctColor(summary.signal_ic.return_60d)}>
                  {summary.signal_ic.return_60d?.toFixed(3) ?? "—"}
                </span>
              </span>
            </div>
          </div>
        </div>
      </details>

      <div className="text-[0.65rem] text-slate-600">
        마지막 갱신 {new Date(summary.generated_at).toLocaleString()}
      </div>
    </div>
  );
}
