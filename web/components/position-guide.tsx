import type { PositionGuidance } from "@/lib/types";

interface Props {
  guidance?: PositionGuidance | null;
  currency?: "USD" | "KRW";
}

function fmtPrice(p: number, currency: "USD" | "KRW"): string {
  if (currency === "KRW") return `₩${Math.round(p).toLocaleString()}`;
  if (p >= 1000) return `$${p.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
  if (p >= 1) return `$${p.toFixed(2)}`;
  return `$${p.toFixed(4)}`;
}

export function PositionGuide({ guidance, currency = "USD" }: Props) {
  if (!guidance) return null;
  const noPosition = guidance.suggested_pct <= 0;
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
      <h3 className="text-sm font-semibold text-white flex items-center gap-2">
        <span>📐 포지션 사이징 가이드</span>
        <span className="text-xs font-normal text-slate-500">
          — ATR(14) × 1% 룰
        </span>
      </h3>
      {noPosition ? (
        <div className="text-sm text-slate-400">
          현 라벨·과열도 기준 신규 진입 비추천. 보유 중이라면 손절선만 참고:
          <div className="mt-2 text-xs text-slate-500">
            손절폭 {(guidance.stop_pct * 100).toFixed(1)}% (entry{" "}
            {fmtPrice(guidance.entry_price, currency)} → stop{" "}
            {fmtPrice(guidance.stop_price, currency)})
          </div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-slate-950/60 rounded p-2">
              <div className="text-xs text-slate-500">권장 비중</div>
              <div className="text-emerald-400 text-lg font-mono tabular-nums">
                {(guidance.suggested_pct * 100).toFixed(1)}%
              </div>
              <div className="text-[0.65rem] text-slate-500">자산 대비</div>
            </div>
            <div className="bg-slate-950/60 rounded p-2">
              <div className="text-xs text-slate-500">손절선 (2-ATR)</div>
              <div className="text-rose-400 text-lg font-mono tabular-nums">
                −{(guidance.stop_pct * 100).toFixed(1)}%
              </div>
              <div className="text-[0.65rem] text-slate-500">
                {fmtPrice(guidance.stop_price, currency)} 이하 도달 시
              </div>
            </div>
          </div>
          <div className="text-xs text-slate-400 leading-relaxed">{guidance.basis}</div>
          <details className="text-xs text-slate-500">
            <summary className="cursor-pointer hover:text-slate-300">
              계산 방식
            </summary>
            <div className="mt-1.5 space-y-1 pl-2 border-l border-slate-800">
              <div>· ATR(14) = {(guidance.atr_pct * 100).toFixed(2)}% (일평균 변동성)</div>
              <div>· 손절폭 = 2 × ATR% (단, 최소 2%)</div>
              <div>· 권장 비중 = (1% / 손절폭) × 라벨·과열도·tier 보정</div>
              <div>· 1번 손절 = 전체 자산의 1% 손실 (1% rule)</div>
              <div>· 캡: 일반 5% / 레버리지 ETF 3%</div>
            </div>
          </details>
        </>
      )}
    </div>
  );
}
