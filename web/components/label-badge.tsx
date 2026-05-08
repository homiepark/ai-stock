import { cn, LABEL_EMOJI, LABEL_LABEL, labelClass } from "@/lib/utils";
import type { LabelText } from "@/lib/types";

export function LabelBadge({
  label,
  size = "md",
  className,
}: {
  label: LabelText | string;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const safe = (label as LabelText) in LABEL_EMOJI ? (label as LabelText) : "HOLD";
  const sizeCls =
    size === "sm" ? "text-[10px] px-1.5 py-0.5" : size === "lg" ? "text-sm px-3 py-1" : "text-xs px-2 py-0.5";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded border font-semibold whitespace-nowrap",
        sizeCls,
        labelClass(safe),
        className,
      )}
    >
      <span>{LABEL_EMOJI[safe]}</span>
      <span>{LABEL_LABEL[safe]}</span>
    </span>
  );
}
