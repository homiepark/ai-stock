import type { AssetClass, LabelText, Verdict } from "@/lib/types";
import { LABEL_EMOJI, LABEL_LABEL, labelClass } from "@/lib/utils";

const ORDER: LabelText[] = ["STRONG_BUY", "ACCUMULATE", "HOLD", "TRIM", "AVOID"];

export function HeroStats({
  verdicts,
  date,
  title,
  subtitle,
  asset,
}: {
  verdicts: Verdict[];
  date: string;
  title: string;
  subtitle: string;
  asset: AssetClass;
}) {
  const hrefFor = (ticker: string) =>
    asset === "coin" ? `/coin/${ticker}` : `/stock/${ticker}`;
  const total = verdicts.length;

  const counts: Record<LabelText, number> = {
    STRONG_BUY: 0,
    ACCUMULATE: 0,
    HOLD: 0,
    TRIM: 0,
    AVOID: 0,
  };
  let scoreSum = 0;
  for (const v of verdicts) {
    counts[(v.label as LabelText) in counts ? (v.label as LabelText) : "HOLD"] += 1;
    scoreSum += v.scores.composite;
  }
  const avgScore = total > 0 ? scoreSum / total : 0;

  // Top 1 strong buy and worst avoid by composite — surface tiles
  const topBuy = verdicts
    .filter((v) => v.label === "STRONG_BUY")
    .sort((a, b) => b.scores.composite - a.scores.composite)[0];
  const worstAvoid = verdicts
    .filter((v) => v.label === "AVOID")
    .sort((a, b) => a.scores.composite - b.scores.composite)[0];

  // Sentiment label based on the proportion of bullish vs bearish
  const bullish = counts.STRONG_BUY + counts.ACCUMULATE;
  const bearish = counts.TRIM + counts.AVOID;
  const sentiment =
    bullish - bearish > total * 0.2
      ? { text: "강세", color: "text-emerald-400", emoji: "🚀" }
      : bullish - bearish > 0
        ? { text: "약강세", color: "text-emerald-300", emoji: "📈" }
        : bearish - bullish > total * 0.2
          ? { text: "약세", color: "text-rose-400", emoji: "📉" }
          : { text: "중립", color: "text-slate-300", emoji: "⚖️" };

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-xs text-slate-500 mb-1 font-mono">{date}</div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">{title}</h1>
          <p className="text-sm text-slate-400 mt-1">{subtitle}</p>
        </div>
        <div className={`text-right ${sentiment.color}`}>
          <div className="text-xs text-slate-500">오늘의 시장 분위기</div>
          <div className="text-2xl font-bold tabular-nums">
            {sentiment.emoji} {sentiment.text}
          </div>
          <div className="text-xs text-slate-500 mt-0.5">
            평균 점수 <span className="font-mono">{avgScore.toFixed(1)}</span>
          </div>
        </div>
      </div>

      {/* Label distribution bar — visual at a glance */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
          <span className="uppercase tracking-wider">라벨 분포</span>
          <span className="font-mono">{total}종목</span>
        </div>
        <div className="flex h-3 rounded-full overflow-hidden">
          {ORDER.map((label) => {
            const n = counts[label];
            const pct = total > 0 ? (n / total) * 100 : 0;
            if (n === 0) return null;
            return (
              <div
                key={label}
                title={`${LABEL_LABEL[label]}: ${n}`}
                style={{ width: `${pct}%` }}
                className={`${labelClass(label)} border-r border-slate-900 last:border-r-0`}
              />
            );
          })}
        </div>
        <div className="mt-3 grid grid-cols-5 gap-2 text-center">
          {ORDER.map((label) => {
            const n = counts[label];
            const pct = total > 0 ? (n / total) * 100 : 0;
            return (
              <div key={label} className="space-y-0.5">
                <div className="text-base">{LABEL_EMOJI[label]}</div>
                <div className="text-lg font-mono font-semibold text-white tabular-nums">
                  {n}
                </div>
                <div className="text-[10px] text-slate-500 font-mono">
                  {pct.toFixed(0)}%
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Best buy / worst avoid quick tiles */}
      {(topBuy || worstAvoid) && (
        <div className="grid sm:grid-cols-2 gap-3">
          {topBuy && (
            <a
              href={hrefFor(topBuy.ticker)}
              className="bg-emerald-950/40 border border-emerald-900/60 rounded-lg p-3 hover:bg-emerald-950/60 transition-colors block"
            >
              <div className="text-xs text-emerald-400 uppercase tracking-wider mb-1">
                🟢 오늘의 STRONG BUY
              </div>
              <div className="flex items-baseline justify-between">
                <div>
                  <div className="text-base font-semibold text-white">{topBuy.name}</div>
                  <div className="text-xs text-slate-500 font-mono">{topBuy.ticker}</div>
                </div>
                <div className="text-2xl font-mono font-bold text-emerald-300 tabular-nums">
                  {topBuy.scores.composite.toFixed(0)}
                </div>
              </div>
            </a>
          )}
          {worstAvoid && (
            <a
              href={hrefFor(worstAvoid.ticker)}
              className="bg-rose-950/30 border border-rose-900/60 rounded-lg p-3 hover:bg-rose-950/50 transition-colors block"
            >
              <div className="text-xs text-rose-400 uppercase tracking-wider mb-1">
                🔴 회피 권고
              </div>
              <div className="flex items-baseline justify-between">
                <div>
                  <div className="text-base font-semibold text-white">{worstAvoid.name}</div>
                  <div className="text-xs text-slate-500 font-mono">{worstAvoid.ticker}</div>
                </div>
                <div className="text-2xl font-mono font-bold text-rose-300 tabular-nums">
                  {worstAvoid.scores.composite.toFixed(0)}
                </div>
              </div>
            </a>
          )}
        </div>
      )}
    </section>
  );
}
