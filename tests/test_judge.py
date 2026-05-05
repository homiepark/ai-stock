from ai_stock.judge.scorer import compose
from ai_stock.judge.verdict import _parse_response, generate_narrative
from ai_stock.signals.long_term import long_term_signal
from ai_stock.signals.mid_term import mid_term_signal
from ai_stock.signals.short_term import short_term_signal


def test_compose_label_thresholds(synthetic_prices, sample_fundamentals):
    short = short_term_signal(synthetic_prices())
    mid = mid_term_signal(synthetic_prices(), sample_fundamentals)
    long = long_term_signal(sample_fundamentals)
    v = compose(short, mid, long)
    assert v.label in {"STRONG_BUY", "ACCUMULATE", "HOLD", "TRIM", "AVOID"}
    assert 0.0 <= v.composite_score <= 100.0


def test_parse_response_well_formed():
    text = """LABEL: STRONG_BUY
SUMMARY: 단기 모멘텀 강력. 펀더멘털 견조.
ENTRY: 1차 950, 2차 900 분할 진입
RISKS: 매크로 유동성 반전, 컨센 하향
TRIGGER: 2026-05-25 어닝
"""
    n = _parse_response(text, fallback_label="HOLD")
    assert n.label == "STRONG_BUY"
    assert "단기" in n.summary
    assert "950" in n.entry_guide
    assert "어닝" in n.next_trigger


def test_parse_response_falls_back_on_garbage():
    n = _parse_response("garbage with no fields", fallback_label="HOLD")
    assert n.label == "HOLD"


def test_generate_narrative_stub_when_no_api_key(monkeypatch, sample_stock, synthetic_prices, sample_fundamentals):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    short = short_term_signal(synthetic_prices())
    mid = mid_term_signal(synthetic_prices(), sample_fundamentals)
    long = long_term_signal(sample_fundamentals)
    v = compose(short, mid, long)
    n = generate_narrative(sample_stock, v, short, mid, long, metrics={"last_close": 100},
                           fundamentals=sample_fundamentals, recent_news=[])
    assert n.label == v.label
    assert "LLM 미연결" in n.summary
