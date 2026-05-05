"""Configuration loading."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"


@dataclass
class Stock:
    ticker: str
    country: str
    tier: str
    name: str
    note: str = ""
    theme: str = ""

    @property
    def display(self) -> str:
        return f"{self.name} ({self.ticker})"


@dataclass
class Theme:
    key: str
    name: str
    thesis: str
    stocks: list[Stock] = field(default_factory=list)


@dataclass
class Universe:
    themes: dict[str, Theme]
    macro: list[dict[str, str]]

    def all_stocks(self) -> list[Stock]:
        return [s for t in self.themes.values() for s in t.stocks]

    def find(self, ticker: str) -> Stock | None:
        for s in self.all_stocks():
            if s.ticker == ticker or s.name == ticker:
                return s
        return None


def load_universe(path: Path | None = None) -> Universe:
    p = path or (CONFIG_DIR / "universe.yaml")
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    themes: dict[str, Theme] = {}
    for key, t in raw["themes"].items():
        stocks = [Stock(theme=key, **s) for s in t["stocks"]]
        themes[key] = Theme(key=key, name=t["name"], thesis=t["thesis"], stocks=stocks)
    return Universe(themes=themes, macro=raw.get("macro", []))


def load_settings(path: Path | None = None) -> dict[str, Any]:
    p = path or (CONFIG_DIR / "settings.yaml")
    return yaml.safe_load(p.read_text(encoding="utf-8"))
