import { loadLatest } from "@/lib/data";
import { MacroGrid } from "@/components/macro-grid";
import { ThemeRankings } from "@/components/theme-rankings";
import { FocusCards } from "@/components/focus-cards";
import { VerdictMatrix } from "@/components/verdict-matrix";
import { NewsList } from "@/components/news-list";
import { LabelChangesPanel } from "@/components/label-changes";
import { SearchPalette } from "@/components/search-palette";

export const revalidate = 3600;

export default async function StockDashboard() {
  const ctx = await loadLatest("stock");

  if (ctx.universe_size === 0) {
    return (
      <div className="text-center py-20 space-y-4">
        <h1 className="text-2xl font-semibold text-white">데이터 준비 중</h1>
        <p className="text-slate-400 text-sm">
          Python 파이프라인이 첫 빌드를 완료하면 여기에 리포트가 표시됩니다.
          <br />
          로컬에선{" "}
          <code className="bg-slate-800 px-1 py-0.5 rounded text-emerald-400">
            uv run ai-stock daily
          </code>{" "}
          실행 후 새로고침.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <SearchPalette
        verdicts={ctx.verdicts}
        themeRankings={ctx.theme_rankings}
        asset="stock"
      />

      <section className="space-y-2">
        <div className="text-sm text-slate-400">{ctx.date}</div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white">
          AI 투자 일일 리포트
        </h1>
        <p className="text-sm text-slate-400">
          워치리스트 {ctx.universe_size}종목 · 미국 {ctx.us_count} / 한국{" "}
          {ctx.kr_count} · 4대 자산 계층 + Embodied AI 추적
        </p>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-white mb-3">📊 매크로 스냅샷</h2>
        <MacroGrid macro={ctx.macro} />
      </section>

      <section>
        <h2 className="text-lg font-semibold text-white mb-3">
          🚀 테마 랭킹 — 오늘의 자금 흐름
        </h2>
        <ThemeRankings rankings={ctx.theme_rankings} />
      </section>

      <section>
        <h2 className="text-lg font-semibold text-white mb-3">
          ⭐ 오늘의 주목 종목 Top 5
        </h2>
        <FocusCards verdicts={ctx.verdicts} asset="stock" />
      </section>

      <section>
        <h2 className="text-lg font-semibold text-white mb-3">
          🎯 종합 판정 매트릭스{" "}
          <span className="text-xs font-normal text-slate-500">
            — 검색·테마·라벨로 필터, 컬럼 클릭으로 정렬, 행 클릭으로 상세
          </span>
        </h2>
        <VerdictMatrix verdicts={ctx.verdicts} asset="stock" />
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
