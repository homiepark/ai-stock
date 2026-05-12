import type { DerivativesContext, MultiTFContext } from "@/lib/types";

interface Props {
  derivatives?: DerivativesContext | null;
  multiTf?: MultiTFContext | null;
}

const TREND_DOT: Record<string, string> = {
  up: "🟢",
  down: "🔴",
  neutral: "⚪",
};

const TF_LABEL: Record<string, string> = {
  weekly: "주봉",
  daily: "일봉",
  "4h": "4시간봉",
};

const BIAS_COLOR: Record<string, string> = {
  long_crowded: "text-rose-300",
  short_crowded: "text-yellow-300",
  neutral: "text-slate-300",
  bullish: "text-emerald-300",
  bearish: "text-rose-300",
  mixed: "text-slate-300",
};

function fmtPct(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const x = (v * 100).toFixed(digits);
  return v > 0 ? `+${x}%` : `${x}%`;
}

export function MarketStructure({ derivatives, multiTf }: Props) {
  if (!derivatives && !multiTf) return null;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-4">
      <h3 className="text-sm font-semibold text-white flex items-center gap-2">
        🏗 시장 구조
        <span className="text-xs font-normal text-slate-500">
          — 멀티 TF + 파생상품 포지셔닝
        </span>
      </h3>

      {multiTf && (
        <div>
          <div className="flex items-center justify-between mb-2 text-xs">
            <span className="text-slate-500">멀티 타임프레임 추세</span>
            <span className={`font-medium ${BIAS_COLOR[multiTf.bias]}`}>
              {multiTf.bias === "bullish"
                ? "▲ 정렬 강세"
                : multiTf.bias === "bearish"
                ? "▼ 정렬 약세"
                : "↔ 혼조"}
              <span className="ml-1 text-slate-500">
                (score {multiTf.bias_score > 0 ? "+" : ""}
                {multiTf.bias_score})
              </span>
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            {multiTf.timeframes.map((tf) => (
              <div
                key={tf.timeframe}
                className="bg-slate-950/60 rounded p-2"
                title={tf.note}
              >
                <div className="flex items-center justify-between">
                  <span className="text-slate-300 font-medium">
                    {TF_LABEL[tf.timeframe] || tf.timeframe}
                  </span>
                  <span>{TREND_DOT[tf.trend]}</span>
                </div>
                <div className="text-slate-500 text-[0.65rem] mt-0.5">
                  RSI {tf.rsi !== null ? tf.rsi.toFixed(0) : "—"}
                  {tf.ma_50 !== null && tf.last_close !== null && (
                    <>
                      {" "}· {tf.last_close > tf.ma_50 ? ">" : "<"}50MA
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
          <div className="text-xs text-slate-400 mt-2">{multiTf.note}</div>
        </div>
      )}

      {derivatives && (
        <div className="border-t border-slate-800/60 pt-3">
          <div className="flex items-center justify-between mb-2 text-xs">
            <span className="text-slate-500">
              파생상품 ({derivatives.symbol} · Binance)
            </span>
            <span className={`font-medium ${BIAS_COLOR[derivatives.bias]}`}>
              {derivatives.bias === "long_crowded"
                ? "🔥 롱 과밀"
                : derivatives.bias === "short_crowded"
                ? "❄️ 숏 과밀"
                : "⚖️ 균형"}
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="bg-slate-950/60 rounded p-2">
              <div className="text-slate-500 text-[0.65rem]">Funding (8h)</div>
              <div
                className={`font-mono tabular-nums font-medium ${
                  derivatives.funding_rate_8h > 0
                    ? "text-rose-300"
                    : derivatives.funding_rate_8h < 0
                    ? "text-yellow-300"
                    : "text-slate-300"
                }`}
              >
                {fmtPct(derivatives.funding_rate_8h, 4)}
              </div>
              <div className="text-[0.6rem] text-slate-500">
                연환산 {fmtPct(derivatives.funding_rate_annual, 1)}
              </div>
            </div>
            <div className="bg-slate-950/60 rounded p-2">
              <div className="text-slate-500 text-[0.65rem]">L/S Ratio</div>
              <div className="font-mono tabular-nums text-slate-200">
                {derivatives.long_short_ratio !== null
                  ? derivatives.long_short_ratio.toFixed(2)
                  : "—"}
              </div>
              <div className="text-[0.6rem] text-slate-500">
                {derivatives.long_short_ratio !== null
                  ? derivatives.long_short_ratio > 1
                    ? "롱 비중 우세"
                    : "숏 비중 우세"
                  : "데이터 없음"}
              </div>
            </div>
            <div className="bg-slate-950/60 rounded p-2">
              <div className="text-slate-500 text-[0.65rem]">OI 24h</div>
              <div
                className={`font-mono tabular-nums ${
                  derivatives.oi_change_24h_pct !== null
                    ? derivatives.oi_change_24h_pct > 0
                      ? "text-sky-300"
                      : "text-slate-400"
                    : "text-slate-500"
                }`}
              >
                {fmtPct(derivatives.oi_change_24h_pct, 1)}
              </div>
              <div className="text-[0.6rem] text-slate-500">
                {derivatives.oi_change_24h_pct === null
                  ? "—"
                  : derivatives.oi_change_24h_pct > 0
                  ? "포지션 진입"
                  : "포지션 청산"}
              </div>
            </div>
          </div>
          <div className="text-xs text-slate-400 mt-2">{derivatives.bias_note}</div>
        </div>
      )}
    </div>
  );
}
