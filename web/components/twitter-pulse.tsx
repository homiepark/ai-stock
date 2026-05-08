"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Heart, Repeat2 } from "lucide-react";
import type { SocialPulse } from "@/lib/types";

const CATEGORY_LABEL: Record<string, string> = {
  memecoin_alpha: "밈코인 알파",
  trader: "베테랑 트레이더",
  analyst: "데이터 분석가",
  founder: "창립자·운영자",
  narrative: "내러티브·트렌드",
};

export function TwitterPulse({ social }: { social: SocialPulse }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <section>
      <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
        🔥 트위터 펄스
        <span className="text-xs font-normal text-slate-500">
          — ApeWisdom 집계 + 큐레이션 인플루언서 {social.influencer_count}명
        </span>
      </h2>

      {/* Trending coins */}
      {social.trending && social.trending.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden mb-3">
          <div className="px-4 py-2 bg-slate-950 text-xs text-slate-400 uppercase tracking-wider">
            급상승 멘션 (24h 델타)
          </div>
          <div className="divide-y divide-slate-800">
            {social.trending.map((t) => (
              <div
                key={t.ticker}
                className="px-4 py-2.5 flex items-center gap-3"
              >
                <span className="text-xs text-slate-500 font-mono w-6">
                  #{t.rank}
                </span>
                <span className="font-medium text-white w-20 truncate flex-shrink-0">
                  {t.ticker}
                </span>
                <span className="text-xs text-slate-400 truncate flex-1">
                  {t.name}
                </span>
                <span className="text-xs font-mono text-slate-300 tabular-nums">
                  {t.mentions} 멘션
                </span>
                <span
                  className={`text-xs font-mono tabular-nums w-16 text-right ${
                    t.delta_pct > 50
                      ? "text-emerald-400 font-semibold"
                      : t.delta_pct > 0
                        ? "text-emerald-400"
                        : t.delta_pct < 0
                          ? "text-rose-400"
                          : "text-slate-500"
                  }`}
                >
                  {t.delta_pct > 0 ? "+" : ""}
                  {t.delta_pct.toFixed(0)}%
                </span>
                {t.is_rising ? (
                  <span className="px-1.5 py-0.5 text-[10px] rounded bg-amber-500/20 text-amber-400 border border-amber-500/40 font-medium whitespace-nowrap">
                    🔥 RISING
                  </span>
                ) : (
                  <span className="w-16" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Influencer tweet samples (if Sorsa active) */}
      {social.tweet_samples && social.tweet_samples.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden mb-3">
          <div className="px-4 py-2 bg-slate-950 text-xs text-slate-400 uppercase tracking-wider flex items-center justify-between">
            <span>
              인플루언서 최신 트윗 ({social.tweet_samples.length}건)
            </span>
            {social.source_status.sorsa === "ok" && (
              <span className="text-emerald-400 text-[10px] normal-case">
                via Sorsa API
              </span>
            )}
          </div>
          <div className="divide-y divide-slate-800">
            {social.tweet_samples.slice(0, 12).map((tw, i) => (
              <a
                key={i}
                href={tw.link}
                target="_blank"
                rel="noopener"
                className="block px-4 py-2.5 hover:bg-slate-800/50"
              >
                <div className="flex items-center gap-2 mb-1 text-xs">
                  {tw.name && (
                    <span className="text-white font-medium">{tw.name}</span>
                  )}
                  <span className="text-sky-400 font-mono">@{tw.handle}</span>
                  {tw.weight && (
                    <span className="text-slate-500">·{tw.weight}</span>
                  )}
                  {tw.score && (
                    <span className="px-1 py-0.5 rounded bg-slate-800 text-emerald-400 text-[10px] font-mono">
                      Sorsa {tw.score.toFixed(0)}
                    </span>
                  )}
                  <span className="text-slate-500 ml-auto">{tw.ts}</span>
                </div>
                <p className="text-sm text-slate-300 leading-snug mb-1">
                  {tw.text}
                </p>
                {(tw.likes || tw.retweets) && (
                  <div className="text-[11px] text-slate-500 font-mono tabular-nums flex items-center gap-3">
                    {tw.likes ? (
                      <span className="flex items-center gap-1">
                        <Heart className="size-3" /> {tw.likes}
                      </span>
                    ) : null}
                    {tw.retweets ? (
                      <span className="flex items-center gap-1">
                        <Repeat2 className="size-3" /> {tw.retweets}
                      </span>
                    ) : null}
                  </div>
                )}
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Influencer roster */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg">
        <button
          onClick={() => setExpanded((v) => !v)}
          className="w-full px-4 py-2.5 flex items-center justify-between text-xs text-slate-400 hover:text-white"
        >
          <span>
            📋 추적 중인 인플루언서 명단 ({social.influencer_count}명)
          </span>
          {expanded ? (
            <ChevronUp className="size-4" />
          ) : (
            <ChevronDown className="size-4" />
          )}
        </button>
        {expanded && (
          <div className="px-4 pb-3 pt-1 space-y-3">
            {Object.entries(social.influencer_categories).map(
              ([cat, members]) => (
                <div key={cat}>
                  <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">
                    {CATEGORY_LABEL[cat] || cat} ({members.length})
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {members.map((m) => (
                      <a
                        key={m.handle}
                        href={`https://x.com/${m.handle}`}
                        target="_blank"
                        rel="noopener"
                        title={m.note}
                        className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white"
                      >
                        {m.name}{" "}
                        <span className="text-slate-500">·{m.weight}</span>
                      </a>
                    ))}
                  </div>
                </div>
              ),
            )}
          </div>
        )}
      </div>

      {/* Source status */}
      <p className="text-xs text-slate-500 mt-2">
        데이터 소스: Sorsa API{" "}
        <span className="font-mono">
          {social.source_status.sorsa === "ok"
            ? "🟢"
            : social.source_status.sorsa === "disabled"
              ? "⚪ 비활성"
              : social.source_status.sorsa === "no_key"
                ? "🔑 키 없음"
                : "🔴"}
        </span>{" "}
        · ApeWisdom{" "}
        <span className="font-mono">
          {social.source_status.apewisdom === "ok" ? "🟢" : "🔴"}
        </span>
        <span className="ml-1">
          — Sorsa $49~199/월로 인플루언서 실시간 트윗 추적 가능.{" "}
          <a
            href="https://github.com/homiepark/ai-stock/blob/main/docs/SOCIAL_TRACKING.md"
            className="underline hover:text-slate-300"
          >
            자세히
          </a>
        </span>
      </p>
    </section>
  );
}
