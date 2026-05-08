import { loadLatest } from "@/lib/data";
import { MacroGrid } from "@/components/macro-grid";
import { ThemeRankings } from "@/components/theme-rankings";
import { FocusCards } from "@/components/focus-cards";
import { VerdictMatrix } from "@/components/verdict-matrix";
import { NewsList } from "@/components/news-list";
import { LabelChangesPanel } from "@/components/label-changes";
import { TwitterPulse } from "@/components/twitter-pulse";
import { SearchPalette } from "@/components/search-palette";

export const revalidate = 3600;

export default async function CoinDashboard() {
  const ctx = await loadLatest("coin");

  if (ctx.universe_size === 0) {
    return (
      <div className="text-center py-20 space-y-4">
        <h1 className="text-2xl font-semibold text-white">데이터 준비 중</h1>
        <p className="text-slate-400 text-sm">
          코인 데이터는 첫 빌드 후 표시됩니다.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <SearchPalette
        verdicts={ctx.verdicts}
        themeRankings={ctx.theme_rankings}
        asset="coin"
      />

      <section className="space-y-2">
        <div className="text-sm text-slate-400">{ctx.date}</div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white">
          AI 코인 일일 리포트
        </h1>
        <p className="text-sm text-slate-400">
          워치리스트 {ctx.universe_size}코인 · 6대 매집 기준(기관·실사용·거래량·시대흐름·생태계·매출 실체)
        </p>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-white mb-3">📊 글로벌 스냅샷</h2>
        <MacroGrid macro={ctx.macro} />
      </section>

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

      {ctx.social && <TwitterPulse social={ctx.social} />}

      <section>
        <h2 className="text-lg font-semibold text-white mb-3">
          🎯 종합 판정 매트릭스{" "}
          <span className="text-xs font-normal text-slate-500">
            — 검색·테마·라벨 필터 + 컬럼 정렬
          </span>
        </h2>
        <VerdictMatrix verdicts={ctx.verdicts} asset="coin" />
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <section>
          <h2 className="text-lg font-semibold text-white mb-3">📰 뉴스</h2>
          <NewsList news={ctx.top_news} />
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
