import type { TradePlan } from "@/lib/types";

interface Props {
  plan?: TradePlan | null;
  currency?: "USD" | "KRW";
}

function fmtPrice(p: number, currency: "USD" | "KRW"): string {
  if (currency === "KRW") return `₩${Math.round(p).toLocaleString()}`;
  if (p >= 1000) return `$${p.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
  if (p >= 1) return `$${p.toFixed(2)}`;
  return `$${p.toFixed(4)}`;
}

function confidenceLabel(c: number): { label: string; color: string } {
  if (c >= 70) return { label: "강함", color: "text-emerald-400" };
  if (c >= 45) return { label: "보통", color: "text-yellow-400" };
  return { label: "약함", color: "text-slate-400" };
}

export function TradePlanCard({ plan, currency = "USD" }: Props) {
  if (!plan) return null;

  if (!plan.actionable) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-2">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          🎯 Trade Plan
          <span className="text-xs font-normal text-slate-500">
            — confluence-based LONG setup
          </span>
        </h3>
        <div className="text-sm text-slate-300">현재 setup 약함 — 관망 권고.</div>
        <div className="text-xs text-slate-500">{plan.rationale}</div>
      </div>
    );
  }

  const c = confidenceLabel(plan.confidence);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
      <div className="flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          🎯 Trade Plan
          <span className="text-xs font-normal text-slate-500">
            — confluence-based LONG setup
          </span>
        </h3>
        <span className="text-xs">
          신뢰도{" "}
          <span className={`font-mono font-semibold ${c.color}`}>{plan.confidence}</span>
          <span className={`ml-1 ${c.color}`}>({c.label})</span>
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 text-xs">
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded p-2">
          <div className="text-emerald-400 font-medium mb-0.5">진입 zone</div>
          <div className="text-white font-mono tabular-nums">
            {fmtPrice(plan.entry, currency)}
          </div>
          <div className="text-[0.65rem] text-slate-500">
            {fmtPrice(plan.entry_low, currency)} ~ {fmtPrice(plan.entry_high, currency)}
          </div>
        </div>
        <div className="bg-rose-500/10 border border-rose-500/30 rounded p-2">
          <div className="text-rose-400 font-medium mb-0.5">손절선</div>
          <div className="text-white font-mono tabular-nums">
            {fmtPrice(plan.stop_loss, currency)}
          </div>
          <div className="text-[0.65rem] text-slate-500">
            −{(plan.stop_pct * 100).toFixed(1)}% (1.5×ATR 버퍼)
          </div>
        </div>
        <div className="bg-sky-500/10 border border-sky-500/30 rounded p-2">
          <div className="text-sky-400 font-medium mb-0.5">ATR(14)</div>
          <div className="text-white font-mono tabular-nums">
            {(plan.atr_pct * 100).toFixed(2)}%
          </div>
          <div className="text-[0.65rem] text-slate-500">일평균 변동성</div>
        </div>
      </div>

      {plan.targets.length > 0 && (
        <div>
          <div className="text-xs text-slate-500 mb-1">익절 타겟 (분할: 50/30/20%)</div>
          <div className="space-y-1">
            {plan.targets.map((t, i) => (
              <div
                key={i}
                className="flex items-center justify-between bg-slate-950/60 rounded px-2 py-1.5 text-xs"
              >
                <span className="text-emerald-300 font-medium">{t.label}</span>
                <span className="text-white font-mono tabular-nums">
                  {fmtPrice(t.price, currency)}
                </span>
                <span className="text-slate-400 font-mono tabular-nums">R:R {t.rr.toFixed(1)}</span>
                <span className="text-[0.65rem] text-slate-500">
                  conf {t.count}/시그널 weight {t.weight.toFixed(1)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="text-xs text-slate-300 leading-relaxed">{plan.rationale}</div>

      <div className="text-xs text-rose-300/80 border-l-2 border-rose-500/40 pl-2">
        ⚠️ 무효화: {plan.invalidation}
      </div>

      {plan.zones.length > 0 && (
        <details className="text-xs text-slate-500">
          <summary className="cursor-pointer hover:text-slate-300">
            Confluence zone 전체 ({plan.zones.length}개)
          </summary>
          <div className="mt-2 space-y-2 pl-2 border-l border-slate-800">
            {plan.zones.slice(0, 8).map((z, i) => (
              <div key={i}>
                <div className="flex justify-between text-slate-300">
                  <span className="font-mono tabular-nums">
                    {fmtPrice(z.center, currency)}
                  </span>
                  <span>
                    시그널 {z.count} · weight {z.weight.toFixed(2)}
                  </span>
                </div>
                <div className="text-[0.65rem] text-slate-600">
                  {z.signals.map((s) => s.label).join(" · ")}
                </div>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
