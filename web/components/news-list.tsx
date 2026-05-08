import type { NewsItem } from "@/lib/types";

export function NewsList({ news }: { news: NewsItem[] }) {
  if (!news || news.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 text-center text-slate-500 text-sm">
        워치리스트 종목 관련 뉴스 없음
      </div>
    );
  }
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg divide-y divide-slate-800">
      {news.map((n, i) => (
        <a
          key={i}
          href={n.link}
          target="_blank"
          rel="noopener"
          className="block px-4 py-3 hover:bg-slate-800/50 transition-colors"
        >
          <div className="text-sm text-white">{n.title}</div>
          <div className="mt-1 flex flex-wrap gap-1.5 text-xs">
            {n.matched_names?.slice(0, 3).map((name, j) => (
              <span
                key={j}
                className="px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded"
              >
                {name}
              </span>
            ))}
            <span className="text-slate-500 ml-auto">{n.source}</span>
          </div>
        </a>
      ))}
    </div>
  );
}
