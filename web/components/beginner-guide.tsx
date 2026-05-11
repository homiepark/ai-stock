"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, BookOpen } from "lucide-react";

const SECTIONS: Array<{ q: string; a: React.ReactNode }> = [
  {
    q: "🟢 STRONG BUY / 🟡 ACCUMULATE / ⚪ HOLD / 🟠 TRIM / 🔴 AVOID 는 무슨 뜻?",
    a: (
      <>
        <p>5단계 매수 판정입니다:</p>
        <ul className="list-disc list-inside space-y-0.5 mt-1">
          <li>
            <strong className="text-emerald-400">🟢 STRONG BUY</strong> —
            단기·중기·장기 모두 우호적. 분할매수 시작 검토.
          </li>
          <li>
            <strong className="text-yellow-400">🟡 ACCUMULATE</strong> —
            중장기는 좋지만 단기 약간 부담. 천천히 모아가기.
          </li>
          <li>
            <strong className="text-slate-300">⚪ HOLD</strong> — 중립. 신호 대기.
          </li>
          <li>
            <strong className="text-orange-400">🟠 TRIM</strong> — 일부 차익실현 검토.
          </li>
          <li>
            <strong className="text-rose-400">🔴 AVOID</strong> — 회피. 신규 진입 자제.
          </li>
        </ul>
      </>
    ),
  },
  {
    q: "🔥 과열도는 뭔가요? 라벨이랑 뭐가 달라요?",
    a: (
      <>
        <p>
          <strong>라벨</strong>은 "이 종목이 좋은가?"의 답이고,{" "}
          <strong>과열도</strong>는 "지금 사도 되는가?"의 답입니다. 좋은 종목도
          이미 너무 올랐으면 단기에 -10~20% 조정이 올 수 있어요.
        </p>
        <ul className="list-disc list-inside space-y-0.5 mt-1">
          <li>🟢 정상 (0~30): 진입 OK</li>
          <li>🟡 약과열 (30~55): 분할매수로만 — 한 번에 들어가지 마세요</li>
          <li>🟠 과열 (55~75): 조정 기다리기</li>
          <li>🔴 극과열 (75+): 회피 또는 차익실현</li>
        </ul>
      </>
    ),
  },
  {
    q: "단기·중기·장기 점수 차이는?",
    a: (
      <>
        <ul className="list-disc list-inside space-y-1">
          <li>
            <strong>단기 (1~12주)</strong>: 차트 신호 — RSI, 이동평균선, 거래량.
            "지금 진입해도 단기 손실 안 날까?"
          </li>
          <li>
            <strong>중기 (3~12개월)</strong>: 실적·컨센서스 흐름. "이 회사 분기
            실적이 잘 나오나?"
          </li>
          <li>
            <strong>장기 (1~5년)</strong>: 매출 성장률·마진·밸류에이션. "10배 갈
            자격이 있는 회사인가?"
          </li>
        </ul>
        <p className="mt-2 text-slate-400">
          이 세 점수를 가중평균(0.25 / 0.35 / 0.40)해서 종합 점수가 나옵니다.
        </p>
      </>
    ),
  },
  {
    q: "분할매수가 뭐예요? 어떻게 하나요?",
    a: (
      <>
        <p>
          한 번에 다 사지 않고 <strong>가격대를 나눠서 여러 번 사는 전략</strong>.
          평균 단가를 낮추고 떨어질 때 추가 매수 여력을 남기는 방법.
        </p>
        <p className="mt-2">
          <strong>예시</strong>: NVDA를 1000만원어치 사고 싶다면 →
        </p>
        <ul className="list-disc list-inside space-y-0.5 mt-1">
          <li>1차: 지금 가격에 334만원 (1/3)</li>
          <li>2차: -5% 떨어지면 333만원 (1/3)</li>
          <li>3차: -10% 떨어지면 333만원 (1/3)</li>
        </ul>
        <p className="mt-2 text-slate-400">
          더 떨어지지 않고 바로 올라가면? 처음 1/3만 잡았어도 수익은 발생.
          반대로 -10%까지 떨어지면 평균 단가가 더 낮아져서 안정적.
        </p>
      </>
    ),
  },
  {
    q: "레버리지 ETF (TQQQ, SOXL 등)는 뭔가요? 사도 되나요?",
    a: (
      <>
        <p>
          기초 자산의 <strong>일일 수익률</strong>을 2~3배로 추종하는 ETF.
          예: QQQ가 하루에 +1% 가면 TQQQ는 +3%, -1%면 -3%.
        </p>
        <p className="mt-2 text-rose-400 font-medium">
          ⚠️ 주의할 점:
        </p>
        <ul className="list-disc list-inside space-y-0.5 mt-1">
          <li>
            <strong>일일</strong> 수익률 추종 — 장기 보유 시{" "}
            <strong>음의 복리 (volatility decay)</strong>로 손실 누적
          </li>
          <li>횡보장에선 기초 자산이 제자리여도 레버리지 ETF는 야금야금 빠짐</li>
          <li>단기 강한 추세장에서만 진가 발휘</li>
          <li>자산의 5~10% 이하만 베팅 권장, 손절 라인 명확히</li>
        </ul>
        <p className="mt-2 text-slate-400">
          텐베거를 노리는 장기 투자엔 부적합. 단기 트레이딩용.
        </p>
      </>
    ),
  },
  {
    q: "텐베거 (10-bagger)? 뭐예요?",
    a: (
      <p>
        주가가 <strong>10배 오른 종목</strong>. 피터 린치가 만든 용어. 1만원에
        사서 10만원이 되는 거. 보통 5~10년에 걸쳐 일어남. 사이클 초·중반에 진입
        + 끝까지 보유해야 가능. 이 시스템의 <strong>장기 점수</strong>가
        텐베거 후보를 찾는 데 쓰임.
      </p>
    ),
  },
];

export function BeginnerGuide() {
  const [expanded, setExpanded] = useState(false);
  return (
    <details
      className="bg-slate-900/50 border border-slate-800 rounded-lg group"
      open={expanded}
    >
      <summary
        className="px-4 py-3 cursor-pointer text-sm flex items-center gap-2 hover:bg-slate-900/80 rounded-lg list-none [&::-webkit-details-marker]:hidden"
        onClick={(e) => {
          e.preventDefault();
          setExpanded((v) => !v);
        }}
      >
        <BookOpen className="size-4 text-sky-400" />
        <span className="text-slate-300 font-medium">초보자 가이드</span>
        <span className="text-slate-500 text-xs">
          — 라벨·과열도·분할매수 등 핵심 용어 한 번에
        </span>
        <span className="ml-auto text-slate-500">
          {expanded ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
        </span>
      </summary>
      <div className="border-t border-slate-800 divide-y divide-slate-800">
        {SECTIONS.map((s, i) => (
          <div key={i} className="px-4 py-3 space-y-2">
            <div className="text-sm font-medium text-white">{s.q}</div>
            <div className="text-sm text-slate-300 leading-relaxed">{s.a}</div>
          </div>
        ))}
        <div className="px-4 py-3 text-xs text-slate-500 bg-slate-950/50">
          더 많은 용어 →{" "}
          <a
            href="https://github.com/homiepark/ai-stock/blob/main/docs/GLOSSARY.md"
            target="_blank"
            rel="noopener"
            className="text-sky-400 hover:text-sky-300 underline"
          >
            docs/GLOSSARY.md
          </a>
        </div>
      </div>
    </details>
  );
}
