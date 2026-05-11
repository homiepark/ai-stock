"""English → Korean translator for news headlines + summaries.

Uses Claude Haiku (small/fast). Each translation is cached by article URL
so we only pay once per article — overall cost is dominated by daily
new articles (~50/day, sub-cent each).

Falls back silently to the original English text if:
  - ANTHROPIC_API_KEY is missing
  - anthropic SDK is unavailable
  - the request fails

So the news pipeline never breaks because translation failed.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re

from ai_stock.data.cache import DiskCache

log = logging.getLogger(__name__)

_TRANSLATE_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 600

_SYSTEM_PROMPT = (
    "당신은 금융·기술 뉴스 번역가입니다. 영문 헤드라인과 요약을 "
    "자연스러운 한국어로 번역합니다. 규칙:\n"
    "- 고유명사(회사명·티커·인명)는 영어 원문 유지\n"
    "- 단위·숫자·통화기호 그대로\n"
    "- 의역 OK. 직역체 금지.\n"
    "- 정확히 두 줄 출력:\n"
    "  TITLE: <번역된 헤드라인>\n"
    "  SUMMARY: <번역된 요약>\n"
    "- 다른 설명·전후 텍스트 금지."
)


def _looks_english(text: str) -> bool:
    """Heuristic: contains zero Hangul AND mostly ASCII letters."""
    if not text:
        return False
    if re.search(r"[가-힯]", text):  # Hangul block
        return False
    letters = re.findall(r"[A-Za-z]", text)
    if len(letters) < 5:  # too short to be a meaningful English headline
        return False
    return True


def _cache_key(link: str, title: str) -> str:
    """Stable key per article. Use link when present, else hash the title."""
    seed = link or title
    return "translate_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _parse_response(text: str) -> tuple[str, str] | None:
    """Pull TITLE:/SUMMARY: lines back out of the model response."""
    title_m = re.search(r"^TITLE:\s*(.+?)$", text, re.MULTILINE)
    summary_m = re.search(r"^SUMMARY:\s*(.+?)$", text, re.MULTILINE | re.DOTALL)
    if not title_m or not summary_m:
        return None
    return title_m.group(1).strip(), summary_m.group(1).strip()


def translate_news(
    title: str,
    summary: str,
    link: str = "",
    cache: DiskCache | None = None,
) -> tuple[str, str]:
    """Return (title_ko, summary_ko). Falls back to originals on any failure.

    Only translates when the input looks English (no Hangul present).
    Otherwise returns the input unchanged (so Korean RSS feeds pass through).
    """
    if not _looks_english(title) and not _looks_english(summary):
        return title, summary

    if cache is not None:
        cached = cache.get_json(_cache_key(link, title))
        if cached and "title" in cached and "summary" in cached:
            return cached["title"], cached["summary"]

    if not os.getenv("ANTHROPIC_API_KEY"):
        return title, summary

    try:
        import anthropic
    except ImportError:
        return title, summary

    user_text = f"TITLE: {title}\nSUMMARY: {summary[:600]}"
    try:
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=_TRANSLATE_MODEL,
            max_tokens=_MAX_TOKENS,
            system=[{
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_text}],
        )
        out_text = "".join(
            b.text for b in resp.content if getattr(b, "type", None) == "text"
        )
    except Exception as e:
        log.warning("news translation failed: %s", e)
        return title, summary

    parsed = _parse_response(out_text)
    if not parsed:
        log.warning("could not parse translation response: %r", out_text[:200])
        return title, summary
    title_ko, summary_ko = parsed
    if cache is not None:
        cache.set_json(
            _cache_key(link, title),
            {"title": title_ko, "summary": summary_ko},
        )
    return title_ko, summary_ko
