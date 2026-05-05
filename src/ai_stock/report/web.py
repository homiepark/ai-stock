"""HTML site generator. Renders the same daily context as the Markdown report
but as a self-contained static site under `site/`, suitable for GitHub Pages.

Layout written:
    site/
      index.html         → today's report (latest)
      archive.html       → list of all past reports
      <YYYY-MM-DD>.html  → each historical report

`build_site` rewrites the index every day from `context`. Past day .html files
are kept untouched once written, so the archive accumulates over time.
"""
from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ai_stock.config import REPO_ROOT

log = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _render_report(env: Environment, context: dict[str, Any]) -> str:
    return env.get_template("site_report.html.j2").render(**context)


def _render_archive(env: Environment, entries: list[dict[str, str]],
                    version: str, generated_at: str) -> str:
    return env.get_template("site_archive.html.j2").render(
        entries=entries, version=version, generated_at=generated_at,
    )


def _scan_existing_dates(site_dir: Path) -> list[str]:
    dates: set[str] = set()
    for p in site_dir.glob("*.html"):
        name = p.stem
        if len(name) == 10 and name.count("-") == 2 and name.replace("-", "").isdigit():
            dates.add(name)
    return sorted(dates, reverse=True)


def build_site(
    context: dict[str, Any],
    site_dir: Path | None = None,
) -> Path:
    """Render index.html for today + per-date archive page + archive listing.

    Returns the site root directory.
    """
    site_dir = site_dir or (REPO_ROOT / "site")
    site_dir.mkdir(parents=True, exist_ok=True)

    env = _env()
    today = context["date"]

    # Today's page
    today_html = _render_report(env, context)
    (site_dir / "index.html").write_text(today_html, encoding="utf-8")
    (site_dir / f"{today}.html").write_text(today_html, encoding="utf-8")

    # Archive
    dates = _scan_existing_dates(site_dir)
    if today not in dates:
        dates.insert(0, today)
        dates.sort(reverse=True)
    entries = [{"date": d, "filename": f"{d}.html"} for d in dates]
    (site_dir / "archive.html").write_text(
        _render_archive(env, entries, context["version"], context["generated_at"]),
        encoding="utf-8",
    )

    # GitHub Pages: a CNAME-less plain build. Disable Jekyll processing so paths
    # starting with `_` (none here, but future-proof) are served as-is.
    (site_dir / ".nojekyll").write_text("", encoding="utf-8")

    log.info("Wrote site → %s (index, %s.html, archive.html, %d total entries)",
             site_dir, today, len(entries))
    return site_dir
