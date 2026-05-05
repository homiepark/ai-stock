"""LLM-narrated verdict using Anthropic Claude API.

Combines quantitative scores with qualitative narrative grounded in:
  - Theme thesis (cached, rarely changes)
  - Company-specific thesis + fundamentals (cached per stock)
  - Daily quantitative signals + recent news (volatile, not cached)

Uses prompt caching to keep recurring per-stock context cheap. Falls back to a
deterministic stub when the Anthropic client is unavailable so the report
generator still produces output for testing.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from ai_stock.config import Stock
from ai_stock.judge.scorer import LABEL_EMOJI, CompositeVerdict
from ai_stock.signals.long_term import LongTermResult
from ai_stock.signals.mid_term import MidTermResult
from ai_stock.signals.short_term import ShortTermResult

log = logging.getLogger(__name__)


SYSTEM_PROMPT = """당신은 미국·한국 주식에 대해 실전 트레이딩 의견을 제시하는 시니어 포트폴리오 매니저입니다.

다음 원칙을 지킵니다:
1. 단기(1~12주) / 중기(3~12개월) / 장기(1~5년) 시간대를 명확히 구분합니다.
2. 정량 점수를 출발점으로 삼되, 점수만 반복하지 않고 "왜" 그런지를 시장 맥락·뉴스·산업 사이클로 연결합니다.
3. 5단계 라벨(STRONG_BUY / ACCUMULATE / HOLD / TRIM / AVOID) 중 하나로 단정 짓고, 분할매수 진입가 가이드를 구체적 가격으로 제시합니다.
4. 리스크 1~2가지를 명시합니다.
5. 다음 트리거 이벤트(어닝, 컨퍼런스, 가이던스 등)를 1가지 적습니다.
6. 한국어로 작성하되, 종목명·티커·고유명사는 원문 그대로 둡니다.
7. 분량은 2~4문장. 군더더기 없이.
"""


@dataclass
class Narrative:
    label: str  # 5단계 중 하나 — 정량 라벨과 다를 수 있음 (LLM 판단)
    summary: str
    entry_guide: str
    risks: str
    next_trigger: str


def _build_user_prompt(
    stock: Stock,
    composite: CompositeVerdict,
    short: ShortTermResult,
    mid: MidTermResult,
    long: LongTermResult,
    metrics: dict[str, Any],
    fundamentals: dict[str, Any],
    recent_news: list[dict[str, Any]],
) -> str:
    news_block = "\n".join(
        f"- {n.get('title', '')[:140]}" for n in recent_news[:5]
    ) or "- (워치리스트 관련 뉴스 없음)"

    last_close = metrics.get("last_close")
    ma50 = metrics.get("ma50")
    ma200 = metrics.get("ma200")
    rsi14 = metrics.get("rsi14")
    ret_60d = metrics.get("ret_60d")

    return f"""[종목] {stock.name} ({stock.ticker}, {stock.country}) — {stock.theme}
[투자 논거(고정)] {stock.note}

[정량 점수] 단기 {short.score:.1f} / 중기 {mid.score:.1f} / 장기 {long.score:.1f} → 종합 {composite.composite_score:.1f} ({composite.label})

[기술적 스냅샷]
- 종가: {last_close}
- 50일 이평: {ma50}, 200일 이평: {ma200}
- RSI(14): {rsi14}
- 60일 수익률: {ret_60d}

[단기 근거] {' / '.join(short.rationale)}
[중기 근거] {' / '.join(mid.rationale)}
[장기 근거] {' / '.join(long.rationale)}

[펀더멘털 일부]
- EV/Sales: {fundamentals.get('ev_to_sales')}
- PER: {fundamentals.get('pe')}, PEG: {fundamentals.get('peg')}

[최근 뉴스 헤드라인]
{news_block}

위 정보를 바탕으로 다음을 출력하세요(꼭 이 형식 유지):

LABEL: <STRONG_BUY|ACCUMULATE|HOLD|TRIM|AVOID>
SUMMARY: <2~3문장. 단/중/장 종합 판단의 핵심 근거>
ENTRY: <분할매수 1차/2차 가격 또는 관망 조건. 구체적 숫자>
RISKS: <1~2가지 리스크>
TRIGGER: <다음 가격 변동을 일으킬 가능성 큰 이벤트 1개>
"""


def _parse_response(text: str, fallback_label: str) -> Narrative:
    fields = {"LABEL": fallback_label, "SUMMARY": "", "ENTRY": "", "RISKS": "", "TRIGGER": ""}
    current = None
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        for key in fields:
            prefix = f"{key}:"
            if s.startswith(prefix):
                fields[key] = s[len(prefix):].strip()
                current = key
                break
        else:
            if current and fields[current]:
                fields[current] += " " + s
    label = fields["LABEL"].split()[0].upper() if fields["LABEL"] else fallback_label
    if label not in {"STRONG_BUY", "ACCUMULATE", "HOLD", "TRIM", "AVOID"}:
        label = fallback_label
    return Narrative(label=label, summary=fields["SUMMARY"], entry_guide=fields["ENTRY"],
                     risks=fields["RISKS"], next_trigger=fields["TRIGGER"])


def _stub_narrative(stock: Stock, composite: CompositeVerdict, short: ShortTermResult,
                    mid: MidTermResult, long: LongTermResult) -> Narrative:
    """Used when no API key is configured — keeps reports useful for local dev/testing."""
    summary = (
        f"{stock.name}: 정량 종합 {composite.composite_score:.0f}점, 라벨 {composite.label}. "
        f"단기 {short.score:.0f} / 중기 {mid.score:.0f} / 장기 {long.score:.0f}. "
        f"(LLM 미연결 — 정량 요약만 표기)"
    )
    return Narrative(
        label=composite.label,
        summary=summary,
        entry_guide="API 키 미설정 — 진입 가이드 자동 생성 불가",
        risks="LLM 서술 미생성. 정량 점수만 참고할 것",
        next_trigger="다음 어닝 발표",
    )


def generate_narrative(
    stock: Stock,
    composite: CompositeVerdict,
    short: ShortTermResult,
    mid: MidTermResult,
    long: LongTermResult,
    metrics: dict[str, Any],
    fundamentals: dict[str, Any],
    recent_news: list[dict[str, Any]],
    model: str = "claude-opus-4-7",
    use_caching: bool = True,
) -> Narrative:
    """Generate a per-stock narrative verdict via Claude.

    Caching strategy: system prompt + the company's thesis line are stable across
    daily runs, so we put a cache breakpoint after the static thesis block. The
    daily volatile section (prices, news) follows the breakpoint and is not
    cached.
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        return _stub_narrative(stock, composite, short, mid, long)

    try:
        import anthropic
    except ImportError:
        log.warning("anthropic SDK not installed; falling back to stub narrative")
        return _stub_narrative(stock, composite, short, mid, long)

    user_prompt = _build_user_prompt(stock, composite, short, mid, long, metrics, fundamentals, recent_news)

    # Split user content so the per-stock thesis can be cached but the volatile
    # daily snapshot is not. We split at the "[기술적 스냅샷]" marker.
    split_marker = "[기술적 스냅샷]"
    if use_caching and split_marker in user_prompt:
        stable, volatile = user_prompt.split(split_marker, 1)
        user_content = [
            {"type": "text", "text": stable, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": split_marker + volatile},
        ]
    else:
        user_content = [{"type": "text", "text": user_prompt}]

    client = anthropic.Anthropic()
    try:
        response = client.messages.create(
            model=model,
            max_tokens=1000,
            system=[{
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_content}],
        )
    except Exception as e:
        log.warning("Claude API call failed for %s: %s", stock.ticker, e)
        return _stub_narrative(stock, composite, short, mid, long)

    text = next((b.text for b in response.content if getattr(b, "type", "") == "text"), "")
    return _parse_response(text, fallback_label=composite.label)


def label_with_emoji(label: str) -> str:
    return f"{LABEL_EMOJI.get(label, '⚪')} {label}"
