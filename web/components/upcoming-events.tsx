import type { UpcomingEvent } from "@/lib/types";

interface Props {
  events?: UpcomingEvent[];
  /** Limit on items shown. Default 8 fits one column nicely. */
  limit?: number;
}

const KIND_ICON: Record<UpcomingEvent["kind"], string> = {
  macro: "🌐",
  earnings: "📊",
};

function daysFromNow(iso: string): number {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(iso + "T00:00:00");
  return Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

function relativeLabel(iso: string): string {
  const d = daysFromNow(iso);
  if (d === 0) return "오늘";
  if (d === 1) return "내일";
  if (d < 7) return `D-${d}`;
  return `${d}일 후`;
}

export function UpcomingEvents({ events, limit = 8 }: Props) {
  if (!events || events.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 text-sm text-slate-500 text-center">
        다가오는 일정 없음
      </div>
    );
  }
  const shown = events.slice(0, limit);
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg divide-y divide-slate-800">
      {shown.map((e, i) => (
        <div
          key={`${e.date}-${e.kind}-${e.ticker || e.name}-${i}`}
          className="flex items-center gap-3 px-3 py-2 text-sm"
        >
          <span
            className={`flex-shrink-0 inline-flex items-center justify-center w-12 text-xs font-mono tabular-nums px-1.5 py-0.5 rounded ${
              e.impact === "high"
                ? "bg-amber-500/20 text-amber-300"
                : "bg-slate-800 text-slate-400"
            }`}
            title={e.date}
          >
            {relativeLabel(e.date)}
          </span>
          <span className="text-slate-500 text-xs font-mono tabular-nums hidden sm:inline w-20">
            {e.date.slice(5)}
          </span>
          <span className="flex-shrink-0">{KIND_ICON[e.kind]}</span>
          <span className="flex-1 text-slate-200 truncate">
            {e.name}
            {e.ticker && (
              <span className="ml-1.5 text-xs text-slate-500">({e.ticker})</span>
            )}
          </span>
          {e.note && e.kind === "macro" && (
            <span className="text-xs text-slate-500 hidden md:inline truncate max-w-[40%]">
              {e.note}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
