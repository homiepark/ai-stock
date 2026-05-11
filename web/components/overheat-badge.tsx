import { Flame } from "lucide-react";
import type { Overheat } from "@/lib/types";
import { cn } from "@/lib/utils";

const LEVEL_STYLE: Record<Overheat["level"], string> = {
  normal: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
  mild: "bg-yellow-500/15 text-yellow-300 border-yellow-500/40",
  high: "bg-orange-500/20 text-orange-300 border-orange-500/40",
  extreme: "bg-rose-500/20 text-rose-300 border-rose-500/50",
};

export function OverheatBadge({
  overheat,
  size = "md",
  showLabel = true,
}: {
  overheat: Overheat | null;
  size?: "sm" | "md";
  showLabel?: boolean;
}) {
  if (!overheat) return null;
  const sizeCls = size === "sm" ? "text-[10px] px-1.5 py-0.5" : "text-xs px-2 py-0.5";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded border font-medium whitespace-nowrap",
        sizeCls,
        LEVEL_STYLE[overheat.level],
      )}
      title={overheat.guidance}
    >
      {overheat.level !== "normal" && <Flame className="size-3" />}
      {showLabel ? overheat.label : overheat.emoji}
      <span className="font-mono tabular-nums opacity-70">
        {overheat.score.toFixed(0)}
      </span>
    </span>
  );
}

/**
 * "지금 사도 되나" — combines composite label + overheat into one
 * plain-Korean recommendation that a beginner can act on.
 */
export function BuyTimingGuide({
  label,
  overheat,
}: {
  label: string;
  overheat: Overheat | null;
}) {
  // Determine final guidance from cross-product of label and overheat level
  const isStrongPositive = label === "STRONG_BUY" || label === "ACCUMULATE";
  const isNegative = label === "TRIM" || label === "AVOID";

  let icon: string;
  let title: string;
  let body: string;
  let color: string;

  if (overheat && overheat.level === "extreme") {
    icon = "🛑";
    title = "지금은 진입 자제";
    body = "단기 급등으로 과열 상태. 10~20% 조정을 기다리는 게 안전합니다.";
    color = "bg-rose-950/40 border-rose-900/60";
  } else if (overheat && overheat.level === "high" && isStrongPositive) {
    icon = "⏸️";
    title = "분할매수만 (1/3씩)";
    body =
      "장기 펀더멘털은 좋지만 단기 과열. 한 번에 들어가지 말고 3회 분할 진입하세요. 첫 1/3만 지금, 나머지는 -5%, -10% 떨어질 때.";
    color = "bg-orange-950/30 border-orange-900/50";
  } else if (overheat && overheat.level === "mild" && isStrongPositive) {
    icon = "🟡";
    title = "조심스러운 진입";
    body =
      "약간 과열. 분할매수로 1/2씩 두 번 나눠서. 첫 진입 후 -5% 정도 빠지면 추가 매수.";
    color = "bg-yellow-950/30 border-yellow-900/50";
  } else if (isStrongPositive) {
    icon = "🟢";
    title = "진입 OK";
    body =
      label === "STRONG_BUY"
        ? "단·중·장 모두 우호적이고 과열 신호 없음. 일반 분할매수(1/2씩 두 번)로 진입 검토."
        : "중장기 우호적. 조정 시 또는 지금 분할매수 검토.";
    color = "bg-emerald-950/30 border-emerald-900/50";
  } else if (isNegative) {
    icon = "🚫";
    title = "회피 권고";
    body =
      label === "AVOID"
        ? "펀더멘털 훼손 또는 사이클 후반. 신규 진입 자제, 보유 중이면 손절 또는 차익실현 검토."
        : "단기 과열 + 펀더멘털 정체. 일부 차익실현 검토.";
    color = "bg-rose-950/30 border-rose-900/50";
  } else {
    icon = "⚪";
    title = "관망 / 대기";
    body = "뚜렷한 매수 신호 없음. 본격 진입보다는 워치리스트에 두고 신호 강해질 때 검토.";
    color = "bg-slate-900 border-slate-800";
  }

  return (
    <div className={cn("rounded-lg border p-4 space-y-2", color)}>
      <div className="flex items-start gap-2">
        <span className="text-2xl flex-shrink-0">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-white">{title}</div>
          <p className="text-sm text-slate-300 mt-1 leading-relaxed">{body}</p>
        </div>
      </div>
      {overheat && overheat.flags.length > 0 && (
        <div className="text-xs text-slate-400 pt-2 border-t border-slate-800">
          <div className="font-medium text-slate-500 mb-1">
            과열 신호 {overheat.score.toFixed(0)}/100:
          </div>
          <ul className="space-y-0.5">
            {overheat.flags.map((f, i) => (
              <li key={i}>• {f}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
