import type { MacroSnapshot } from "@/lib/types";
import { changeColor, numFmt, pctFmt } from "@/lib/utils";

export function MacroGrid({ macro }: { macro: MacroSnapshot }) {
  const entries = Object.entries(macro);
  if (entries.length === 0) return null;
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
      {entries.map(([key, m]) => (
        <div key={key} className="bg-slate-900 border border-slate-800 rounded-lg p-3">
          <div className="text-xs text-slate-400 truncate">{m.name}</div>
          <div className="text-lg font-mono font-semibold text-white tabular-nums">
            {numFmt(m.value)}
          </div>
          <div className={`text-xs font-mono tabular-nums ${changeColor(m.change)}`}>
            {pctFmt(m.change)}
          </div>
        </div>
      ))}
    </div>
  );
}
