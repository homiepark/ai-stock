import type { LabelChange } from "@/lib/types";
import { LabelBadge } from "./label-badge";

export function LabelChangesPanel({ changes }: { changes: LabelChange[] }) {
  if (!changes || changes.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 text-center text-slate-500 text-sm">
        어제 대비 라벨 변경 없음
      </div>
    );
  }
  return (
    <ul className="bg-slate-900 border border-slate-800 rounded-lg divide-y divide-slate-800">
      {changes.map((c, i) => (
        <li
          key={i}
          className="px-4 py-2.5 flex flex-wrap items-center gap-3 text-sm"
        >
          <span className="font-medium text-white">{c.name}</span>
          <span className="text-slate-500 font-mono text-xs">{c.ticker}</span>
          <span className="ml-auto flex items-center gap-2">
            <LabelBadge label={c.old_label} size="sm" />
            <span className="text-slate-500">→</span>
            <LabelBadge label={c.new_label} size="sm" />
          </span>
        </li>
      ))}
    </ul>
  );
}
