import Link from "next/link";
import { loadLatest } from "@/lib/data";
import { HeroStats } from "@/components/hero-stats";
import { MacroGrid } from "@/components/macro-grid";
import { ThemeRankings } from "@/components/theme-rankings";
import { FocusCards } from "@/components/focus-cards";
import { Movers } from "@/components/movers";
import { VerdictMatrix } from "@/components/verdict-matrix";
import { NewsList } from "@/components/news-list";
import { LabelChangesPanel } from "@/components/label-changes";
import { SearchPalette } from "@/components/search-palette";

export const revalidate = 3600;

export default async function StockDashboard() {
  const ctx = await loadLatest("stock");

  if (ctx.universe_size === 0) {
    return <EmptyState />;
  }

  const subtitle = `워치리스트 ${ctx.universe_size}종목 · 미국 ${ctx.us_count} / 한국 ${ctx.kr_count} · 4대 자산 계층 + Embodied AI`;

  return (
    <div className="space-y-8">
      <SearchPalette
        verdicts={ctx.verdicts}
        themeRankings={ctx.theme_rankings}
        asset="stock"
      />

      <HeroStats
        verdicts={ctx.verdicts}
        date={ctx.date}
        title="AI 투자 일일 리포트"
        subtitle={subtitle}
        asset="stock"
      />

      <section>
        <h2 className="text-lg font-semibold text-white mb-3">📊 매크로 스냅샷</h2>
        <MacroGrid macro={ctx.macro} />
      </section>

      <Movers verdicts={ctx.verdicts} asset="stock" />

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
            — 검색·테마·라벨 필터, 컬럼 클릭 정렬, 행 클릭 상세
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

function EmptyState() {
  return (
    <div className="max-w-xl mx-auto py-20 text-center space-y-6">
      <div className="text-6xl mb-2">📈</div>
      <h1 className="text-2xl font-semibold text-white">데이터 준비 중</h1>
      <p className="text-slate-400 text-sm leading-relaxed">
        GitHub Actions가 첫 빌드를 마치면 여기에 리포트가 나타납니다.
        <br />
        <strong className="text-slate-300">매주 화~토 한국시간 06:30</strong> 자동 실행돼요.
      </p>
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 text-left text-sm space-y-3">
        <div className="text-xs text-slate-500 uppercase tracking-wider">즉시 데이터 받기</div>
        <ol className="space-y-2 text-slate-300 list-decimal list-inside">
          <li>
            <a
              href="https://github.com/homiepark/ai-stock/actions/workflows/daily-report.yml"
              target="_blank"
              rel="noopener"
              className="text-sky-400 hover:text-sky-300 underline"
            >
              GitHub Actions로 이동
            </a>
          </li>
          <li>오른쪽 위 <code className="bg-slate-800 px-1 rounded">Run workflow</code> 클릭</li>
          <li>3~5분 후 자동으로 이 사이트에 반영</li>
        </ol>
      </div>
      <div className="flex gap-2 justify-center text-sm">
        <Link href="/coins" className="text-slate-400 hover:text-white">
          🪙 코인 탭 보기 →
        </Link>
      </div>
    </div>
  );
}
