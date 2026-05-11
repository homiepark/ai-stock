import Link from "next/link";
import { loadLatest, loadBacktestSummary } from "@/lib/data";
import { HeroStats } from "@/components/hero-stats";
import { MacroGrid } from "@/components/macro-grid";
import { ThemeRankings } from "@/components/theme-rankings";
import { FocusCards } from "@/components/focus-cards";
import { Movers } from "@/components/movers";
import { VerdictMatrix } from "@/components/verdict-matrix";
import { NewsList } from "@/components/news-list";
import { LabelChangesPanel } from "@/components/label-changes";
import { TwitterPulse } from "@/components/twitter-pulse";
import { SearchPalette } from "@/components/search-palette";
import { BeginnerGuide } from "@/components/beginner-guide";
import { UpcomingEvents } from "@/components/upcoming-events";
import { BacktestSummary } from "@/components/backtest-summary";

export const revalidate = 3600;

export default async function CoinDashboard() {
  const ctx = await loadLatest("coin");
  const backtest = await loadBacktestSummary();

  if (ctx.universe_size === 0) {
    return (
      <div className="max-w-xl mx-auto py-20 text-center space-y-6">
        <div className="text-6xl">🪙</div>
        <h1 className="text-2xl font-semibold text-white">코인 데이터 준비 중</h1>
        <p className="text-slate-400 text-sm">
          첫 빌드 후 표시됩니다.{" "}
          <Link href="/" className="text-sky-400 underline">
            주식 탭
          </Link>
          으로 가서 데이터가 있는지 먼저 확인해보세요.
        </p>
      </div>
    );
  }

  const subtitle = `워치리스트 ${ctx.universe_size}코인 · 6대 매집 기준(기관·실사용·거래량·시대흐름·생태계·매출 실체)`;

  return (
    <div className="space-y-8">
      <SearchPalette
        verdicts={ctx.verdicts}
        themeRankings={ctx.theme_rankings}
        asset="coin"
      />

      <HeroStats
        verdicts={ctx.verdicts}
        date={ctx.date}
        title="AI 코인 일일 리포트"
        subtitle={subtitle}
        asset="coin"
      />

      <BeginnerGuide />

      <section>
        <h2 className="text-lg font-semibold text-white mb-3">📊 글로벌 스냅샷</h2>
        <MacroGrid macro={ctx.macro} />
      </section>

      <section>
        <h2 className="text-lg font-semibold text-white mb-3">
          🗓 다가오는 트리거{" "}
          <span className="text-xs font-normal text-slate-500">
            — 14일 내 FOMC·CPI·매크로 이벤트
          </span>
        </h2>
        <UpcomingEvents events={ctx.upcoming_events} />
      </section>

      {ctx.social && <TwitterPulse social={ctx.social} />}

      <Movers verdicts={ctx.verdicts} asset="coin" />

      <section>
        <h2 className="text-lg font-semibold text-white mb-3">
          🚀 테마 랭킹 — 자금 흐름
        </h2>
        <ThemeRankings rankings={ctx.theme_rankings} />
      </section>

      <section>
        <h2 className="text-lg font-semibold text-white mb-3">
          ⭐ 오늘의 주목 코인 Top 5
        </h2>
        <FocusCards verdicts={ctx.verdicts} asset="coin" />
      </section>

      <section>
        <h2 className="text-lg font-semibold text-white mb-3">
          🎯 종합 판정 매트릭스{" "}
          <span className="text-xs font-normal text-slate-500">
            — 검색·테마·라벨 필터 + 컬럼 정렬
          </span>
        </h2>
        <VerdictMatrix verdicts={ctx.verdicts} asset="coin" />
      </section>

      <section>
        <BacktestSummary summary={backtest} />
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <section>
          <h2 className="text-lg font-semibold text-white mb-3">📰 뉴스</h2>
          <NewsList
            news={ctx.top_news}
            themes={ctx.theme_rankings.map((r) => ({
              key: r.theme_key,
              label: r.theme_name.split(/[·(]/)[0].trim(),
            }))}
          />
        </section>
        <section>
          <h2 className="text-lg font-semibold text-white mb-3">
            🔄 어제 대비 라벨 변경
          </h2>
          <LabelChangesPanel changes={ctx.label_changes} />
        </section>
      </div>
    </div>
  );
}
