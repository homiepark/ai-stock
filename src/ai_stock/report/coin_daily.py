"""Coin pipeline — parallel to daily.py but for crypto.

Reuses signals (RSI, MACD, MA, momentum), theme momentum, scorer, and verdict
infra. Differences from stock pipeline:

- No US/KR benchmark for relative strength; uses BTC as the crypto benchmark.
- Fundamentals are price-derived proxies (no PE/PEG for crypto).
- Macro snapshot is global crypto state (BTC dominance, total mcap, ETH/BTC).
- Output paths: reports/daily/coins-YYYY-MM-DD.md, site/coin.html.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ai_stock import __version__
from ai_stock.config import REPO_ROOT, Stock, Universe, load_coin_universe, load_settings
from ai_stock.data.cache import DiskCache
from ai_stock.data.coin_prices import fetch_global_snapshot, fetch_coin_market_caps
from ai_stock.data.fundamentals import fetch_fundamentals
from ai_stock.data.news import fetch_news
from ai_stock.data.prices import fetch_prices
from ai_stock.data.social import assemble_social_pulse
from ai_stock.judge.scorer import compose
from ai_stock.judge.verdict import Narrative, generate_narrative, label_with_emoji
from ai_stock.report.daily import (
    LabelChange, StockResult, _compute_label_changes, _theme_short,
)
from ai_stock.signals.long_term import long_term_signal
from ai_stock.signals.mid_term import mid_term_signal
from ai_stock.signals.overheat import overheat_signal
from ai_stock.signals.short_term import latest_metrics, short_term_signal
from ai_stock.signals.theme import StockMomentum, ThemeRanking, rank_theme, stock_momentum

log = logging.getLogger(__name__)


def assemble_coin_context(
    universe: Universe | None = None,
    settings: dict[str, Any] | None = None,
    today: datetime | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Assemble the daily crypto context dict (parallel to assemble_daily_context)."""
    universe = universe or load_coin_universe()
    settings = settings or load_settings()
    today = today or datetime.utcnow()
    output_dir = output_dir or (REPO_ROOT / "reports" / "daily")

    cache = DiskCache(settings["cache"]["dir"], ttl_hours=settings["cache"]["ttl_hours"])

    log.info("Fetching crypto global snapshot")
    macro = fetch_global_snapshot(cache=cache)

    log.info("Fetching social pulse (ApeWisdom + influencer list)")
    social = assemble_social_pulse(cache=cache)

    # Bulk market-cap fetch for all coins (1 API call)
    all_coins = universe.all_stocks()
    log.info("Bulk fetching market caps for %d coins", len(all_coins))
    cg_ids = [c.coingecko_id for c in all_coins if c.coingecko_id]
    market_caps = fetch_coin_market_caps(cg_ids, cache=cache)

    # BTC as benchmark for relative strength
    btc = next((c for c in all_coins if c.ticker == "BTC"), None)
    btc_prices = fetch_prices(btc, cache=cache) if btc else None

    momentum_by_theme: dict[str, list[StockMomentum]] = {k: [] for k in universe.themes}
    results: list[StockResult] = []

    log.info("Processing %d coins", len(all_coins))
    failed_coins: list[str] = []
    for coin in all_coins:
        try:
            prices = fetch_prices(coin, cache=cache)
            fundamentals = fetch_fundamentals(coin, cache=cache)
            cap = market_caps.get(coin.coingecko_id)

            short = short_term_signal(prices, settings["signals"]["short_term"]["weights"])
            mid = mid_term_signal(prices, fundamentals, btc_prices,
                                  settings["signals"]["mid_term"]["weights"])
            long = long_term_signal(fundamentals, settings["signals"]["long_term"]["weights"])
            composite = compose(short, mid, long, settings["verdict"]["weights"], settings["verdict"]["thresholds"])

            sm = stock_momentum(coin, prices, cap)
            if sm:
                momentum_by_theme[coin.theme].append(sm)

            metrics = latest_metrics(prices)
            overheat = overheat_signal(prices)
            results.append(StockResult(
                stock=coin,
                composite=composite,
                narrative=Narrative(label=composite.label, summary="", entry_guide="", risks="", next_trigger=""),
                metrics=metrics,
                theme_short=_theme_short(universe.themes[coin.theme].name),
                label_emoji=label_with_emoji(composite.label).split()[0],
                overheat=overheat,
            ))
        except Exception as e:
            log.warning("Coin %s (%s) failed: %s; continuing", coin.ticker, coin.coingecko_id, e)
            failed_coins.append(f"{coin.ticker}({coin.coingecko_id})")

    if failed_coins:
        log.warning("Skipped %d coins due to errors: %s",
                    len(failed_coins), ", ".join(failed_coins))

    # Theme rankings
    theme_rankings: list[ThemeRanking] = []
    for key, theme in universe.themes.items():
        members = momentum_by_theme.get(key, [])
        ranking = rank_theme(theme, members,
                             settings["theme"]["weights"], settings["theme"]["leader_weights"])
        theme_rankings.append(ranking)
    theme_rankings.sort(key=lambda r: r.composite_return, reverse=True)

    # News — same RSS feeds as stocks; coin-symbol matching is simpler since
    # tickers (BTC, ETH) appear in headlines unambiguously
    log.info("Fetching news from %d feeds", len(settings["news"]["rss_feeds"]))
    news_items = fetch_news(
        settings["news"]["rss_feeds"], all_coins,
        max_articles=settings["news"]["max_articles_per_run"], cache=cache,
    )
    matched_news = [n for n in news_items if n.matched_tickers]
    top_news = matched_news[: settings["news"]["top_n_in_report"]]

    news_by_ticker: dict[str, list] = {}
    for n in matched_news:
        for t in n.matched_tickers:
            news_by_ticker.setdefault(t, []).append(n)

    # Narratives for top focus coins
    focus_n = settings["report"]["top_n_focus_stocks"]
    focus_results = sorted(results, key=lambda r: r.composite.composite_score, reverse=True)[:focus_n]
    log.info("Generating narratives for top %d focus coins", len(focus_results))
    for r in focus_results:
        prices = fetch_prices(r.stock, cache=cache)
        fundamentals = fetch_fundamentals(r.stock, cache=cache)
        short = short_term_signal(prices, settings["signals"]["short_term"]["weights"])
        mid = mid_term_signal(prices, fundamentals, btc_prices,
                              settings["signals"]["mid_term"]["weights"])
        long = long_term_signal(fundamentals, settings["signals"]["long_term"]["weights"])
        recent = [n.to_dict() for n in news_by_ticker.get(r.stock.ticker, [])[:5]]
        r.narrative = generate_narrative(
            r.stock, r.composite, short, mid, long, r.metrics, fundamentals, recent,
            model=settings["llm"]["model"],
            use_caching=settings["llm"]["use_prompt_caching"],
        )
        r.label_emoji = label_with_emoji(r.narrative.label).split()[0]

    # Position review (parses prior coin reports)
    label_changes = _compute_coin_label_changes(results, output_dir)

    return {
        "date": today.strftime("%Y-%m-%d"),
        "generated_at": today.strftime("%Y-%m-%d %H:%M UTC"),
        "version": __version__,
        "universe_size": len(all_coins),
        "us_count": 0,  # not relevant for coins, but template expects these keys
        "kr_count": 0,
        "asset_class": "coin",  # used by template to switch labels/copy
        "macro": macro,
        "theme_rankings": theme_rankings,
        "verdicts": sorted(results, key=lambda r: r.composite.composite_score, reverse=True),
        "focus": focus_results,
        "top_news": [n.to_dict() for n in top_news],
        "label_changes": label_changes,
        "social": social,
        "_today": today,
    }


def _compute_coin_label_changes(results: list[StockResult], output_dir: Path) -> list[LabelChange]:
    """Same logic as stock label changes but only looks at coins-*.md files."""
    import re
    from ai_stock.judge.scorer import LABEL_EMOJI

    try:
        prior = sorted(output_dir.glob("coins-*.md"), reverse=True)
        if not prior:
            return []
        prev_text = prior[0].read_text(encoding="utf-8")
    except Exception:
        return []

    pattern = re.compile(r"\|\s*\*\*(?P<name>[^*]+)\*\*\s*\(?(?P<ticker>[^)]*)\)?\s*\|.*\|\s*(?P<emoji>[🟢🟡⚪🟠🔴])")
    emoji_to_label = {v: k for k, v in LABEL_EMOJI.items()}
    prev_labels: dict[str, str] = {}
    for m in pattern.finditer(prev_text):
        prev_labels[m.group("ticker").strip()] = emoji_to_label.get(m.group("emoji"), "HOLD")

    changes: list[LabelChange] = []
    for r in results:
        old = prev_labels.get(r.stock.ticker)
        new = r.narrative.label or r.composite.label
        if old and old != new:
            changes.append(LabelChange(stock=r.stock, old_label=old, new_label=new))
    return changes


def build_coin_report(
    universe: Universe | None = None,
    settings: dict[str, Any] | None = None,
    output_dir: Path | None = None,
    today: datetime | None = None,
    context: dict[str, Any] | None = None,
) -> Path:
    """Render the coin Markdown report. Pass `context` to skip pipeline."""
    output_dir = output_dir or (REPO_ROOT / "reports" / "daily")
    output_dir.mkdir(parents=True, exist_ok=True)

    if context is None:
        context = assemble_coin_context(universe=universe, settings=settings,
                                        today=today, output_dir=output_dir)

    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        autoescape=select_autoescape(disabled_extensions=("md", "j2")),
        trim_blocks=True, lstrip_blocks=True,
    )
    template = env.get_template("coin_daily.md.j2")
    rendered = template.render(**context)

    out_path = output_dir / f"coins-{context['date']}.md"
    out_path.write_text(rendered, encoding="utf-8")
    log.info("Wrote coin report → %s", out_path)
    return out_path
