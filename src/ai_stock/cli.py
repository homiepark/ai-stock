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
              help="리포트 출력 디렉토리. 기본: reports/daily/")
def daily(output_dir: Path | None) -> None:
    """일일 리포트 생성. reports/daily/YYYY-MM-DD.md 로 저장."""
    from ai_stock.report.daily import build_daily_report
    path = build_daily_report(output_dir=output_dir)
    click.echo(f"리포트 생성 완료: {path}")


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
