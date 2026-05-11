"""Daily report generation pipeline.

Orchestrates: data fetch → signals → judge → narrative → render Markdown.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ai_stock import __version__
from ai_stock.config import REPO_ROOT, Stock, Universe, load_settings, load_universe
from ai_stock.data.cache import DiskCache
from ai_stock.data.fundamentals import fetch_fundamentals
from ai_stock.data.macro import fetch_macro
from ai_stock.data.news import NewsItem, fetch_news
from ai_stock.data.prices import fetch_market_cap, fetch_prices
from ai_stock.judge.scorer import LABEL_EMOJI, CompositeVerdict, compose
from ai_stock.judge.verdict import Narrative, generate_narrative, label_with_emoji
from ai_stock.signals.long_term import long_term_signal
from ai_stock.signals.mid_term import mid_term_signal
from ai_stock.signals.overheat import OverheatResult, overheat_signal
from ai_stock.signals.sizing import PositionGuidance, position_guidance
from ai_stock.signals.short_term import latest_metrics, short_term_signal
from ai_stock.signals.theme import StockMomentum, ThemeRanking, rank_theme, stock_momentum

log = logging.getLogger(__name__)


@dataclass
class StockResult:
    stock: Stock
    composite: CompositeVerdict
    narrative: Narrative
    metrics: dict[str, Any]
    theme_short: str = ""
    label_emoji: str = ""
    overheat: OverheatResult | None = None
    guidance: PositionGuidance | None = None


@dataclass
class LabelChange:
    stock: Stock
    old_label: str
    new_label: str


def _theme_short(name: str) -> str:
    # "전력·그리드 (AI의 '땅')" → "전력·그리드"
    return re.split(r"[(\s]", name, maxsplit=1)[0].strip() or name


def _benchmark_for(stock: Stock, benchmarks: dict[str, Any]) -> Any:
    return benchmarks.get("US" if stock.country == "US" else "KR")


def assemble_daily_context(
    universe: Universe | None = None,
    settings: dict[str, Any] | None = None,
    today: datetime | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the full pipeline and return a dict ready for any renderer.

    Used by both the Markdown report (`build_daily_report`) and the HTML site
    (`ai_stock.report.web.build_site`). Doing the data fetch + scoring + LLM
    narratives once and rendering N times saves cost.
    """
    universe = universe or load_universe()
    settings = settings or load_settings()
    today = today or datetime.utcnow()
    output_dir = output_dir or (REPO_ROOT / "reports" / "daily")

    cache = DiskCache(settings["cache"]["dir"], ttl_hours=settings["cache"]["ttl_hours"])

    log.info("Fetching macro snapshot")
    macro = fetch_macro(universe.macro, cache=cache)

    log.info("Fetching benchmark prices for relative strength")
    us_bench = fetch_prices(Stock(ticker="^GSPC", country="US", tier="bench", name="S&P 500"), cache=cache)
    kr_bench = fetch_prices(Stock(ticker="^KS11", country="US", tier="bench", name="KOSPI"), cache=cache)
    benchmarks = {"US": us_bench, "KR": kr_bench}

    all_stocks = universe.all_stocks()
    log.info("Processing %d stocks", len(all_stocks))

    momentum_by_theme: dict[str, list[StockMomentum]] = {k: [] for k in universe.themes}
    results: list[StockResult] = []

    for stock in all_stocks:
        prices = fetch_prices(stock, cache=cache)
        fundamentals = fetch_fundamentals(stock, cache=cache)
        market_cap = fetch_market_cap(stock, cache=cache)

        short = short_term_signal(prices, settings["signals"]["short_term"]["weights"])
        mid = mid_term_signal(prices, fundamentals, _benchmark_for(stock, benchmarks),
                              settings["signals"]["mid_term"]["weights"])
        long = long_term_signal(fundamentals, settings["signals"]["long_term"]["weights"])
        composite = compose(short, mid, long, settings["verdict"]["weights"], settings["verdict"]["thresholds"])

        sm = stock_momentum(stock, prices, market_cap)
        if sm:
            momentum_by_theme[stock.theme].append(sm)

        metrics = latest_metrics(prices)
        overheat = overheat_signal(prices)
        guidance = position_guidance(
            prices,
            label=composite.label,
            overheat_level=overheat.level if overheat else "normal",
            tier=stock.tier,
            is_leveraged=(stock.theme == "leveraged"),
        )
        results.append(StockResult(
            stock=stock,
            composite=composite,
            narrative=Narrative(label=composite.label, summary="", entry_guide="", risks="", next_trigger=""),
            metrics=metrics,
            theme_short=_theme_short(universe.themes[stock.theme].name),
            label_emoji=label_with_emoji(composite.label).split()[0],
            overheat=overheat,
            guidance=guidance,
        ))

    # Theme rankings
    theme_rankings: list[ThemeRanking] = []
    for key, theme in universe.themes.items():
        members = momentum_by_theme.get(key, [])
        ranking = rank_theme(theme, members,
                             settings["theme"]["weights"], settings["theme"]["leader_weights"])
        theme_rankings.append(ranking)
    theme_rankings.sort(key=lambda r: r.composite_return, reverse=True)

    # News fetch + per-stock attribution
    log.info("Fetching news from %d feeds", len(settings["news"]["rss_feeds"]))
    news_items = fetch_news(
        settings["news"]["rss_feeds"], all_stocks,
        max_articles=settings["news"]["max_articles_per_run"], cache=cache,
    )
    matched_news = [n for n in news_items if n.matched_tickers]
    top_news = matched_news[: settings["news"]["top_n_in_report"]]

    news_by_ticker: dict[str, list[NewsItem]] = {}
    for n in matched_news:
        for t in n.matched_tickers:
            news_by_ticker.setdefault(t, []).append(n)

    # Narratives for top focus stocks
    focus_n = settings["report"]["top_n_focus_stocks"]
    focus_results = sorted(results, key=lambda r: r.composite.composite_score, reverse=True)[:focus_n]
    log.info("Generating narratives for top %d focus stocks", len(focus_results))
    for r in focus_results:
        try:
            prices = fetch_prices(r.stock, cache=cache)
            fundamentals = fetch_fundamentals(r.stock, cache=cache)
            short = short_term_signal(prices, settings["signals"]["short_term"]["weights"])
            mid = mid_term_signal(prices, fundamentals, _benchmark_for(r.stock, benchmarks),
                                  settings["signals"]["mid_term"]["weights"])
            long = long_term_signal(fundamentals, settings["signals"]["long_term"]["weights"])
            recent = [n.to_dict() for n in news_by_ticker.get(r.stock.ticker, [])[:5]]
            r.narrative = generate_narrative(
                r.stock, r.composite, short, mid, long, r.metrics, fundamentals, recent,
                model=settings["llm"]["model"],
                use_caching=settings["llm"]["use_prompt_caching"],
            )
            r.label_emoji = label_with_emoji(r.narrative.label).split()[0]
        except Exception as e:
            log.warning("Narrative gen failed for %s: %s; keeping quant label",
                        r.stock.ticker, e)

    # Position review
    label_changes = _compute_label_changes(results, output_dir)

    # Upcoming macro + earnings calendar (next 14 days)
    try:
        from ai_stock.data.calendar import upcoming_events
        events = upcoming_events(stocks=all_stocks, today=today.date(), cache=cache)
    except Exception as e:
        log.warning("calendar fetch failed: %s", e)
        events = []

    us_count = sum(1 for s in all_stocks if s.country == "US")
    kr_count = len(all_stocks) - us_count

    return {
        "date": today.strftime("%Y-%m-%d"),
        "generated_at": today.strftime("%Y-%m-%d %H:%M UTC"),
        "version": __version__,
        "universe_size": len(all_stocks),
        "us_count": us_count,
        "kr_count": kr_count,
        "macro": macro,
        "theme_rankings": theme_rankings,
        "verdicts": sorted(results, key=lambda r: r.composite.composite_score, reverse=True),
        "focus": focus_results,
        "top_news": [n.to_dict() for n in top_news],
        "label_changes": label_changes,
        "upcoming_events": events,
        "_today": today,
    }


def build_daily_report(
    universe: Universe | None = None,
    settings: dict[str, Any] | None = None,
    output_dir: Path | None = None,
    today: datetime | None = None,
    context: dict[str, Any] | None = None,
) -> Path:
    """Render the daily Markdown report.

    Pass `context` from `assemble_daily_context()` to skip re-running the pipeline.
    """
    output_dir = output_dir or (REPO_ROOT / "reports" / "daily")
    output_dir.mkdir(parents=True, exist_ok=True)

    if context is None:
        context = assemble_daily_context(universe=universe, settings=settings,
                                         today=today, output_dir=output_dir)

    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        autoescape=select_autoescape(disabled_extensions=("md", "j2")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("daily.md.j2")
    rendered = template.render(**context)

    out_path = output_dir / f"{context['date']}.md"
    out_path.write_text(rendered, encoding="utf-8")
    log.info("Wrote report → %s", out_path)
    return out_path


_LABEL_ROW_RE = re.compile(r"\|\s*\*\*(?P<name>[^*]+)\*\*\s*\(?(?P<ticker>[^)]*)\)?\s*\|.*\|\s*(?P<emoji>[🟢🟡⚪🟠🔴])")


def _compute_label_changes(results: list[StockResult], output_dir: Path) -> list[LabelChange]:
    """Best-effort: parse yesterday's report and diff labels.

    Failure here should never crash the daily run — return empty on any error.
    """
    try:
        prior = sorted([p for p in output_dir.glob("*.md")], reverse=True)
        if len(prior) < 1:
            return []
        # Most recent that is older than today's eventual output (just take the latest)
        prev_text = prior[0].read_text(encoding="utf-8")
    except Exception:
        return []

    emoji_to_label = {v: k for k, v in LABEL_EMOJI.items()}
    prev_labels: dict[str, str] = {}
    for m in _LABEL_ROW_RE.finditer(prev_text):
        ticker = m.group("ticker").strip()
        prev_labels[ticker] = emoji_to_label.get(m.group("emoji"), "HOLD")

    changes: list[LabelChange] = []
    for r in results:
        old = prev_labels.get(r.stock.ticker)
        new = r.narrative.label or r.composite.label
        if old and old != new:
            changes.append(LabelChange(stock=r.stock, old_label=old, new_label=new))
    return changes
