"""Lead scoring: turn website signals into a sales-priority score.

The idea: shops whose web presence is weakest (no site, free builder,
not mobile friendly, stale) benefit most from a new website, so they
rank highest as outreach targets.
"""

from __future__ import annotations

from dataclasses import dataclass

from .checker import SiteCheck

CURRENT_YEAR = 2026


@dataclass
class ScoredLead:
    score: int
    rank: str  # S / A / B / C
    reasons: list[str]


def score_lead(has_website: bool, check: SiteCheck | None) -> ScoredLead:
    score = 0
    reasons: list[str] = []

    if not has_website:
        return ScoredLead(90, "S", ["ホームページなし"])

    assert check is not None
    if not check.reachable:
        score += 40
        reasons.append("サイトに接続できない")
    if check.free_builder:
        score += 25
        reasons.append(f"無料ビルダー利用（{check.free_builder}）")
    if check.reachable and not check.has_viewport:
        score += 20
        reasons.append("スマホ非対応の可能性（viewportなし）")
    if not check.is_https:
        score += 10
        reasons.append("HTTPS未対応")
    if check.copyright_year and check.copyright_year <= CURRENT_YEAR - 3:
        score += 10
        reasons.append(f"更新が古い可能性（© {check.copyright_year}）")
    if check.reachable and not check.has_tel_link:
        score += 5
        reasons.append("電話発信リンクなし")

    score = min(score, 100)
    if score >= 60:
        rank = "S"
    elif score >= 35:
        rank = "A"
    elif score >= 15:
        rank = "B"
    else:
        rank = "C"
    return ScoredLead(score, rank, reasons)
