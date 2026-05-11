"""News translator unit tests.

We never hit the Anthropic API in tests — both happy and unhappy paths
fall through to the cached / passthrough behavior.
"""
from __future__ import annotations

import ai_stock.data.translator as tr


class _MemoryCache:
    """Tiny in-memory DiskCache stand-in (only the methods translator uses)."""
    def __init__(self) -> None:
        self.store: dict[str, dict] = {}

    def get_json(self, key: str):
        return self.store.get(key)

    def set_json(self, key: str, value: dict) -> None:
        self.store[key] = value


def test_looks_english_detects_hangul():
    assert tr._looks_english("NVIDIA earnings beat expectations") is True
    assert tr._looks_english("엔비디아 실적이 예상을 상회했다") is False
    # mixed → presence of Hangul means NOT English-only
    assert tr._looks_english("NVIDIA 실적 호조") is False
    # too short
    assert tr._looks_english("NVDA") is False
    assert tr._looks_english("") is False


def test_translate_passthrough_for_korean_input(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    title, summary = tr.translate_news(
        "엔비디아 실적 호조", "엔비디아가 전망치를 상회했다", link="x",
    )
    assert title == "엔비디아 실적 호조"
    assert summary == "엔비디아가 전망치를 상회했다"


def test_translate_passthrough_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    title, summary = tr.translate_news(
        "NVIDIA beats estimates", "Q4 revenue jumped 22% YoY", link="x",
    )
    # No API key → return originals untouched
    assert title.startswith("NVIDIA")
    assert "Q4" in summary


def test_translate_uses_cache(monkeypatch):
    """Once a translation is cached, the API is never touched again."""
    cache = _MemoryCache()
    cache.set_json(
        tr._cache_key("https://x.test/1", "NVIDIA beats"),
        {"title": "엔비디아 어닝 호조", "summary": "분기 매출 22% 증가"},
    )

    def boom(*a, **kw):  # if the model is invoked, fail loud
        raise AssertionError("API should not be called on cache hit")
    monkeypatch.setattr(tr, "_parse_response", boom)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anything")

    title, summary = tr.translate_news(
        "NVIDIA beats", "Q4 revenue jumped 22% YoY",
        link="https://x.test/1", cache=cache,
    )
    assert title == "엔비디아 어닝 호조"
    assert summary == "분기 매출 22% 증가"
