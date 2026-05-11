"use client";

import { useState } from "react";
import { Info } from "lucide-react";

// Plain-Korean explanations for technical terms. Hover/tap to learn.
// Keep each entry short — one sentence + one practical takeaway.
const GLOSSARY: Record<string, { title: string; body: string }> = {
  RSI: {
    title: "RSI (상대강도지수)",
    body:
      "최근 14일 동안 얼마나 많이 올랐는지 0~100으로 표시. 70 이상이면 너무 많이 올라서 조정 위험, 30 이하면 너무 많이 떨어져서 반등 가능성.",
  },
  MACD: {
    title: "MACD",
    body:
      "추세 전환을 잡는 지표. 0 위로 올라오면 상승 전환 신호, 0 아래로 내려가면 하락 전환 신호.",
  },
  MA50: {
    title: "50일 이동평균선",
    body:
      "최근 50일 평균 가격을 이은 선. 단기 추세 기준. 주가가 이 선 위에 있으면 단기 상승추세, 아래면 하락추세.",
  },
  MA200: {
    title: "200일 이동평균선",
    body:
      "최근 약 1년 평균 가격. 장기 추세 기준. 주가가 200일선 위면 강세장, 아래면 약세장으로 봄.",
  },
  CAGR: {
    title: "CAGR (연평균 성장률)",
    body:
      "매년 평균 몇 % 성장했는지. 복리 기준. 3년 CAGR 25% = 매년 25%씩 꾸준히 성장 = 약 2배.",
  },
  PER: {
    title: "PER (주가수익비율)",
    body:
      "주가 ÷ 1주당 순이익. 투자한 돈을 회수하는 데 몇 년 걸리는지. 낮을수록 싸지만, 성장률 없이 보면 함정. 일반적으로 15 이하 저평가, 25 이상 고평가.",
  },
  PEG: {
    title: "PEG (성장 보정 PER)",
    body:
      "PER ÷ 성장률. 성장 빠른 회사의 PER이 높아도 PEG가 낮으면 저평가. 1 미만 = 성장 대비 싸다, 2 초과 = 비싸다.",
  },
  EVSales: {
    title: "EV/Sales (매출 대비 기업가치)",
    body:
      "시가총액+부채-현금 ÷ 매출. 적자 기업이나 AI 같은 고성장 기업 평가에 자주 씀. 3 이하 저평가, 15 이상 고평가, 25+ 매우 비쌈.",
  },
  Composite: {
    title: "종합 점수",
    body:
      "단기·중기·장기 점수를 가중평균(0.25 / 0.35 / 0.40)한 0~100 종합 판정. 75 이상 STRONG BUY, 60 이상 ACCUMULATE.",
  },
  Overheat: {
    title: "과열도",
    body:
      "지금 너무 많이 올라서 단기 조정 위험이 있는지. RSI·이격·거래량·모멘텀 종합. 80 이상이면 매수 자제, 30 이하면 진입 OK.",
  },
  VolumeZ: {
    title: "거래량 Z-score",
    body:
      "오늘 거래량이 평소(20일 평균)에서 얼마나 벗어났는지. +2 이상은 평소 대비 폭증 = 관심 급증.",
  },
  HBM: {
    title: "HBM (고대역폭 메모리)",
    body:
      "AI 가속기 옆에 붙는 초고속 메모리. SK하이닉스가 NVIDIA에 1차 공급. 한국이 글로벌 1~2위 점유.",
  },
  CoWoS: {
    title: "CoWoS (첨단 패키징)",
    body:
      "TSMC의 첨단 칩 패키징 기술. NVIDIA H100/B200을 만들려면 필수. 캐파 부족이 AI 칩 공급 병목.",
  },
  RWA: {
    title: "RWA (Real World Asset)",
    body:
      "현실 자산(미국 국채·부동산·주식 등)을 블록체인 토큰으로. 기관 자금 가장 빠르게 유입되는 영역.",
  },
  Leverage: {
    title: "레버리지 ETF",
    body:
      "기초 자산의 일일 수익률을 2~3배로 추종. 상승장에선 폭발적, 횡보·하락장에선 손실 누적(음의 복리). 장기 보유 부적합.",
  },
};

export function Term({
  term,
  children,
  className,
}: {
  term: keyof typeof GLOSSARY | string;
  children?: React.ReactNode;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const entry = GLOSSARY[term as keyof typeof GLOSSARY];
  if (!entry) {
    return <>{children ?? term}</>;
  }

  return (
    <span className="relative inline-block">
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setOpen((v) => !v);
        }}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        className={
          className ??
          "inline-flex items-center gap-0.5 underline decoration-dotted decoration-slate-500 hover:decoration-sky-400 cursor-help"
        }
      >
        {children ?? entry.title}
        <Info className="size-3 text-slate-500" />
      </button>
      {open && (
        <span className="absolute z-40 left-0 top-full mt-1 w-64 p-3 bg-slate-800 border border-slate-700 rounded-lg shadow-xl text-xs text-slate-200 leading-relaxed normal-case font-normal pointer-events-none">
          <span className="block font-semibold text-white mb-1">
            {entry.title}
          </span>
          <span className="block text-slate-300">{entry.body}</span>
        </span>
      )}
    </span>
  );
}
