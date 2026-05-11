import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { LabelText } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function pctFmt(n: number | null | undefined, digits = 2): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  const v = (n * 100).toFixed(digits);
  return n > 0 ? `+${v}%` : `${v}%`;
}

export function changeColor(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "text-slate-500";
  if (n > 0) return "text-emerald-400";
  if (n < 0) return "text-rose-400";
  return "text-slate-500";
}

export function numFmt(n: number | null | undefined, digits = 2): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  if (Math.abs(n) >= 1) return n.toFixed(digits);
  return n.toFixed(4);
}

export function bigNumFmt(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  if (n >= 1e12) return `${(n / 1e12).toFixed(2)}T`;
  if (n >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return String(Math.round(n));
}

export const LABEL_EMOJI: Record<LabelText, string> = {
  STRONG_BUY: "🟢",
  ACCUMULATE: "🟡",
  HOLD: "⚪",
  TRIM: "🟠",
  AVOID: "🔴",
};

export const LABEL_LABEL: Record<LabelText, string> = {
  STRONG_BUY: "STRONG BUY",
  ACCUMULATE: "ACCUMULATE",
  HOLD: "HOLD",
  TRIM: "TRIM",
  AVOID: "AVOID",
};

export function labelClass(label: string): string {
  return `label-${label.toLowerCase()}`;
}

