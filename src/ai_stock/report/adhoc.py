"""Ad-hoc single-stock analysis. Works for ANY ticker, not just the watchlist.

Auto-detects country:
  - 6-digit numeric → KR (KRX)
  - alphabetic → US (yfinance)
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ai_stock import __version__
from ai_stock.config import REPO_ROOT, Stock, load_settings, load_universe
from ai_stock.data.cache import DiskCache
from ai_stock.data.fundamentals import fetch_fundamentals
from ai_stock.data.news import fetch_news
from ai_stock.data.prices import fetch_market_cap, fetch_prices
from ai_stock.judge.scorer import compose
from ai_stock.judge.verdict import generate_narrative, label_with_emoji
from ai_stock.signals.long_term import long_term_signal
from ai_stock.signals.mid_term import mid_term_signal
from ai_stock.signals.short_term import latest_metrics, short_term_signal

log = logging.getLogger(__name__)


def _infer_stock(ticker: str, name: str | None = None) -> Stock:
    ticker = ticker.strip().upper()
    if ticker.isdigit() and len(ticker) == 6:
        country = "KR"
    else:
        country = "US"
    return Stock(
        ticker=ticker,
        country=country,
        tier="adhoc",
        name=name or ticker,
        note="(워치리스트 외 종목 — 임시 분석)",
        theme="adhoc",
    )


def analyze_ticker(
    ticker: str,
    name: str | None = None,
    settings: dict[str, Any] | None = None,
    output_dir: Path | None = None,
) -> Path:
    """Fetch data → score → narrative → write Markdown to reports/adhoc/."""
    settings = settings or load_settings()
    output_dir = output_dir or (REPO_ROOT / "reports" / "adhoc")
    output_dir.mkdir(parents=True, exist_ok=True)
    cache = DiskCache(settings["cache"]["dir"], ttl_hours=settings["cache"]["ttl_hours"])

    # If ticker is in watchlist, reuse its rich metadata (theme, note, name)
    universe = load_universe()
    found = universe.find(ticker)
    stock = found if found else _infer_stock(ticker, name)

    log.info("Fetching data for %s (%s)", stock.ticker, stock.country)
    prices = fetch_prices(stock, cache=cache)
    if prices is None or prices.empty:
        raise RuntimeError(
            f"가격 데이터를 가져올 수 없습니다: {stock.ticker}. "
            f"미국 주식이라면 정확한 티커(예: NVDA), 한국 주식이라면 6자리 코드(예: 005930)를 사용하세요."
        )
    fundamentals = fetch_fundamentals(stock, cache=cache)
    market_cap = fetch_market_cap(stock, cache=cache)

    # Benchmarks for relative strength
    bench_ticker = "^GSPC" if stock.country == "US" else "^KS11"
    bench = fetch_prices(Stock(ticker=bench_ticker, country=stock.country, tier="bench", name="bench"), cache=cache)

    short = short_term_signal(prices, settings["signals"]["short_term"]["weights"])
    mid = mid_term_signal(prices, fundamentals, bench, settings["signals"]["mid_term"]["weights"])
    long = long_term_signal(fundamentals, settings["signals"]["long_term"]["weights"])
    composite = compose(short, mid, long, settings["verdict"]["weights"], settings["verdict"]["thresholds"])
    metrics = latest_metrics(prices)

    # News for this stock only
    news_items = fetch_news(settings["news"]["rss_feeds"], [stock],
                            max_articles=settings["news"]["max_articles_per_run"], cache=cache)
    relevant = [n.to_dict() for n in news_items if n.matched_tickers][:5]

    narrative = generate_narrative(
        stock, composite, short, mid, long, metrics, fundamentals, relevant,
        model=settings["llm"]["model"], use_caching=settings["llm"]["use_prompt_caching"],
    )

    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        autoescape=select_autoescape(disabled_extensions=("md", "j2")),
        trim_blocks=True, lstrip_blocks=True,
    )
    template = env.get_template("adhoc.md.j2")

    today = datetime.utcnow()
    rendered = template.render(
        date=today.strftime("%Y-%m-%d"),
        generated_at=today.strftime("%Y-%m-%d %H:%M UTC"),
        version=__version__,
        stock=stock,
        in_watchlist=found is not None,
        composite=composite,
        short=short, mid=mid, long=long,
        metrics=metrics,
        fundamentals=fundamentals,
        market_cap=market_cap,
        narrative=narrative,
        label_emoji=label_with_emoji(narrative.label).split()[0],
        news=relevant,
    )

    out_path = output_dir / f"{stock.ticker}-{today.strftime('%Y-%m-%d')}.md"
    out_path.write_text(rendered, encoding="utf-8")
    log.info("Wrote ad-hoc report → %s", out_path)
    return out_path
