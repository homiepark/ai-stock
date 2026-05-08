"""CLI: `ai-stock daily` / `ai-stock universe`."""
from __future__ import annotations

import logging
from pathlib import Path

import click
from dotenv import load_dotenv

from ai_stock import __version__
from ai_stock.config import load_universe


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Verbose logging.")
@click.version_option(__version__)
def main(verbose: bool) -> None:
    """ai-stock — AI 투자 일일 분석."""
    load_dotenv()
    _setup_logging(verbose)


@main.command()
@click.option("--output-dir", type=click.Path(path_type=Path), default=None,
              help="Markdown 리포트 출력 디렉토리. 기본: reports/daily/")
@click.option("--site-dir", type=click.Path(path_type=Path), default=None,
              help="HTML 사이트 출력 디렉토리. 기본: site/")
@click.option("--no-site", is_flag=True, help="HTML 사이트 빌드 생략 (Markdown만)")
@click.option("--no-coins", is_flag=True, help="코인 파이프라인 생략 (주식만)")
@click.option("--no-stocks", is_flag=True, help="주식 파이프라인 생략 (코인만)")
def daily(output_dir: Path | None, site_dir: Path | None, no_site: bool,
          no_coins: bool, no_stocks: bool) -> None:
    """일일 리포트 생성. 주식 + 코인 둘 다 빌드.

    Markdown: reports/daily/YYYY-MM-DD.md (주식), reports/daily/coins-YYYY-MM-DD.md (코인)
    HTML:     site/index.html (주식), site/coin.html (코인)
    """
    from ai_stock.report.daily import assemble_daily_context, build_daily_report
    from ai_stock.report.coin_daily import assemble_coin_context, build_coin_report
    from ai_stock.report.web import build_site, build_coin_site

    if not no_stocks:
        click.echo("📈 주식 파이프라인 시작...")
        stock_ctx = assemble_daily_context(output_dir=output_dir)
        md_path = build_daily_report(output_dir=output_dir, context=stock_ctx)
        click.echo(f"  Markdown: {md_path}")
        if not no_site:
            site_path = build_site(stock_ctx, site_dir=site_dir)
            click.echo(f"  HTML:     {site_path / 'index.html'}")

    if not no_coins:
        click.echo("🪙 코인 파이프라인 시작...")
        try:
            coin_ctx = assemble_coin_context(output_dir=output_dir)
            md_path = build_coin_report(output_dir=output_dir, context=coin_ctx)
            click.echo(f"  Markdown: {md_path}")
            if not no_site:
                site_path = build_coin_site(coin_ctx, site_dir=site_dir)
                click.echo(f"  HTML:     {site_path / 'coin.html'}")
        except Exception as e:
            click.echo(f"  ⚠️ 코인 파이프라인 실패 (주식은 정상 완료): {e}", err=True)


@main.command()
def universe() -> None:
    """현재 워치리스트 출력."""
    u = load_universe()
    for theme_key, theme in u.themes.items():
        click.echo(f"\n## {theme.name}")
        click.echo(f"   {theme.thesis}")
        for s in theme.stocks:
            tier_mark = {"leader": "★", "momentum": "▲", "supporting": "·"}.get(s.tier, " ")
            click.echo(f"   {tier_mark} {s.ticker:<8} {s.country:<2} {s.name}")


@main.command()
@click.argument("ticker")
@click.option("--name", default=None, help="종목명. 미지정 시 티커를 그대로 사용.")
@click.option("--output-dir", type=click.Path(path_type=Path), default=None,
              help="리포트 출력 디렉토리. 기본: reports/adhoc/")
def analyze(ticker: str, name: str | None, output_dir: Path | None) -> None:
    """워치리스트 외 종목 임시 분석.

    예시:
        ai-stock analyze NVDA              # 미국 주식
        ai-stock analyze 005930            # 한국 주식 (6자리 코드)
        ai-stock analyze AAPL --name 애플
    """
    from ai_stock.report.adhoc import analyze_ticker
    try:
        path = analyze_ticker(ticker, name=name, output_dir=output_dir)
        click.echo(f"임시 분석 리포트 생성: {path}")
    except RuntimeError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
