import Link from "next/link";
import { loadManifest } from "@/lib/data";

export const revalidate = 3600;

export default async function ArchivePage() {
  const manifest = await loadManifest();

  type Entry = { date: string; type: "stock" | "coin" };
  const entries: Entry[] = [
    ...manifest.stock.map((d) => ({ date: d, type: "stock" as const })),
    ...manifest.coin.map((d) => ({ date: d, type: "coin" as const })),
  ];
  entries.sort((a, b) =>
    a.date === b.date ? a.type.localeCompare(b.type) : b.date.localeCompare(a.date),
  );

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold text-white">📚 리포트 기록</h1>
        <p className="text-sm text-slate-400">
          {entries.length}건 · 최신순 · 주식과 코인 통합
        </p>
      </header>

      {entries.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-8 text-center text-slate-500 text-sm">
          아직 기록이 없습니다. Python 파이프라인이 첫 빌드를 마치면 여기에 표시됩니다.
        </div>
      ) : (
        <ul className="bg-slate-900 border border-slate-800 rounded-lg divide-y divide-slate-800">
          {entries.map((e) => (
            <li key={`${e.type}-${e.date}`}>
              <Link
                href={
                  e.type === "stock" ? `/archive/stock/${e.date}` : `/archive/coin/${e.date}`
                }
                className="flex items-center justify-between px-4 py-3 hover:bg-slate-800/50"
              >
                <span className="flex items-center gap-3">
                  <span className="text-sm">
                    {e.type === "stock" ? "📈 주식" : "🪙 코인"}
                  </span>
                  <span className="font-mono text-white">{e.date}</span>
                </span>
                <span className="text-xs text-slate-500">→</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
