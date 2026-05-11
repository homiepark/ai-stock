import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import type { AssetClass, Verdict } from "@/lib/types";
import { LabelBadge } from "./label-badge";
import { ScoreBars } from "./score-bars";
import { MetricsGrid } from "./metrics-grid";
import { OverheatBadge, BuyTimingGuide } from "./overheat-badge";
import { Term } from "./glossary";
import { LivePriceBadge } from "./live-price-badge";

export function DetailView({
  verdict,
  asset,
}: {
  verdict: Verdict;
  asset: AssetClass;
}) {
  const xUrl =
    asset === "coin"
      ? `https://x.com/search?q=%24${encodeURIComponent(verdict.ticker)}&f=live`
      : `https://x.com/search?q=%24${encodeURIComponent(verdict.ticker)}+OR+%22${encodeURIComponent(verdict.name)}%22&f=live`;
  const cgUrl = verdict.coingecko_id
    ? `https://www.coingecko.com/en/coins/${verdict.coingecko_id}`
    : null;
  const yfUrl =
    asset === "stock" && verdict.country === "US"
      ? `https://finance.yahoo.com/quote/${verdict.ticker}`
      : null;
  const naverUrl =
    asset === "stock" && verdict.country === "KR"
      ? `https://finance.naver.com/item/main.nhn?code=${verdict.ticker}`
      : null;

  const backHref = asset === "stock" ? "/" : "/coins";

  return (
    <div className="space-y-6">
      <Link
        href={backHref}
        className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-white"
      >
        <ArrowLeft className="size-4" />
        대시보드로
      </Link>

      <header className="space-y-2">
        <div className="text-xs text-slate-500">{verdict.theme_short}</div>
        <h1 className="text-3xl font-bold text-white flex flex-wrap items-center gap-3">
          {verdict.name}
          <span className="text-slate-500 font-mono text-xl">
            {verdict.ticker}
          </span>
          <LabelBadge label={verdict.label} size="lg" />
          {verdict.overheat && verdict.overheat.level !== "normal" && (
            <OverheatBadge overheat={verdict.overheat} />
          )}
        </h1>
        <p className="text-sm text-slate-300 max-w-3xl">{verdict.note}</p>
        {(() => {
          const kind =
            asset === "coin"
              ? "coin"
              : verdict.country === "KR"
              ? "stock_kr"
              : "stock_us";
          const symbol =
            asset === "coin" ? verdict.coingecko_id : verdict.ticker;
          if (!symbol) return null;
          return (
            <div className="pt-1">
              <LivePriceBadge symbol={symbol} kind={kind} />
            </div>
          );
        })()}
        <div className="flex flex-wrap gap-2 text-xs">
          <a
            href={xUrl}
            target="_blank"
            rel="noopener"
            className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
          >
            𝕏 검색
          </a>
          {cgUrl && (
            <a
              href={cgUrl}
              target="_blank"
              rel="noopener"
              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
            >
              CoinGecko
            </a>
          )}
          {yfUrl && (
            <a
              href={yfUrl}
              target="_blank"
              rel="noopener"
              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
            >
              Yahoo Finance
            </a>
          )}
          {naverUrl && (
            <a
              href={naverUrl}
              target="_blank"
              rel="noopener"
              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
            >
              네이버금융
            </a>
          )}
          <span className="px-2 py-1 rounded bg-slate-800 text-slate-400">
            등급: {verdict.tier === "leader" ? "★ 대장" : verdict.tier === "momentum" ? "▲ 모멘텀" : "· 후순위"}
          </span>
        </div>
      </header>

      <section>
        <h2 className="text-base font-semibold text-white mb-3">
          🎯 지금 사도 되나? — 매수 타이밍 가이드
        </h2>
        <BuyTimingGuide
          label={verdict.label}
          overheat={verdict.overheat}
        />
      </section>

      <section>
        <h2 className="text-base font-semibold text-white mb-3">
          <Term term="Composite">정량 점수</Term>
        </h2>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <ScoreBars scores={verdict.scores} />
          {verdict.label_quant !== verdict.label && (
            <div className="mt-3 pt-3 border-t border-slate-800 text-xs text-slate-500">
              정량만으로는{" "}
              <LabelBadge label={verdict.label_quant} size="sm" />
              인데, LLM이 뉴스·맥락을 종합해{" "}
              <LabelBadge label={verdict.label} size="sm" /> 로 조정.
            </div>
          )}
        </div>
      </section>

      {(verdict.narrative.summary ||
        verdict.narrative.entry_guide ||
        verdict.narrative.risks ||
        verdict.narrative.next_trigger) && (
        <section>
          <h2 className="text-base font-semibold text-white mb-3">LLM 분석</h2>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-4">
            {verdict.narrative.summary && (
              <p className="text-sm text-slate-200 leading-relaxed">
                {verdict.narrative.summary}
              </p>
            )}
            <div className="grid sm:grid-cols-3 gap-3 text-sm">
              {verdict.narrative.entry_guide && (
                <div>
                  <div className="text-emerald-400 font-medium text-xs mb-1">
                    진입 가이드
                  </div>
                  <div className="text-slate-300">
                    {verdict.narrative.entry_guide}
                  </div>
                </div>
              )}
              {verdict.narrative.risks && (
                <div>
                  <div className="text-rose-400 font-medium text-xs mb-1">
                    리스크
                  </div>
                  <div className="text-slate-300">{verdict.narrative.risks}</div>
                </div>
              )}
              {verdict.narrative.next_trigger && (
                <div>
                  <div className="text-sky-400 font-medium text-xs mb-1">
                    다음 트리거
                  </div>
                  <div className="text-slate-300">
                    {verdict.narrative.next_trigger}
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      <section>
        <h2 className="text-base font-semibold text-white mb-3">기술적 스냅샷</h2>
        <MetricsGrid metrics={verdict.metrics} />
      </section>
    </div>
  );
}
