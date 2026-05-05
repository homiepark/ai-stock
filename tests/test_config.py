from ai_stock.config import load_settings, load_universe


def test_universe_loads():
    u = load_universe()
    assert len(u.themes) >= 4
    assert "semiconductors" in u.themes
    all_stocks = u.all_stocks()
    us = sum(1 for s in all_stocks if s.country == "US")
    kr = sum(1 for s in all_stocks if s.country == "KR")
    # Roughly US 70 / KR 30
    assert us > kr
    assert kr / len(all_stocks) > 0.20


def test_universe_finds_known_tickers():
    u = load_universe()
    assert u.find("NVDA") is not None
    assert u.find("042700") is not None  # 한미반도체


def test_settings_loads():
    s = load_settings()
    assert s["llm"]["model"].startswith("claude-")
    assert s["verdict"]["thresholds"]["strong_buy"] >= s["verdict"]["thresholds"]["accumulate"]
