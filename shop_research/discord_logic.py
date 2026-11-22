"""Discord command parsing and result formatting (pure logic, no discord.py).

Kept separate from bot.py so it can be unit-tested without a bot token.
"""

from __future__ import annotations

from dataclasses import dataclass

from .sources import INDUSTRY_PRESETS

TRIGGER = "!リサーチ"
TRIGGER_ALT = "!research"
HELP_TRIGGERS = ("!ヘルプ", "!help")

MAX_LIMIT = 30
DEFAULT_LIMIT = 20


@dataclass
class ResearchRequest:
    area: str
    industry: str
    limit: int = DEFAULT_LIMIT


def parse_command(content: str) -> ResearchRequest | None:
    """Parse '!リサーチ <エリア> <業種> [件数]'. Returns None if not a trigger."""
    text = content.strip()
    for trigger in (TRIGGER, TRIGGER_ALT):
        if text.startswith(trigger):
            rest = text[len(trigger):].strip()
            break
    else:
        return None

    parts = rest.split()
    if len(parts) < 2:
        raise ValueError("使い方: !リサーチ <エリア> <業種> [件数]（例: !リサーチ 札幌市中央区 カフェ）")
    area, industry = parts[0], parts[1]
    if industry not in INDUSTRY_PRESETS:
        raise ValueError(
            f"未対応の業種です: {industry}\n対応業種: {', '.join(INDUSTRY_PRESETS)}"
        )
    limit = DEFAULT_LIMIT
    if len(parts) >= 3:
        try:
            limit = int(parts[2])
        except ValueError:
            raise ValueError("件数は数字で指定してください（例: !リサーチ 札幌市中央区 カフェ 10）")
        limit = max(1, min(limit, MAX_LIMIT))
    return ResearchRequest(area=area, industry=industry, limit=limit)


def is_help(content: str) -> bool:
    return content.strip() in HELP_TRIGGERS


def help_text() -> str:
    return (
        "**店舗リサーチbot**\n"
        "使い方: `!リサーチ <エリア> <業種> [件数]`\n"
        "例: `!リサーチ 札幌市中央区 カフェ` / `!リサーチ 大阪市北区 美容室 10`\n"
        f"対応業種: {', '.join(INDUSTRY_PRESETS)}\n"
        f"件数は最大{MAX_LIMIT}件。結果は要約＋CSVファイルで返します（1〜3分ほどかかります）。"
    )


def format_summary(area: str, industry: str, rows: list[dict]) -> str:
    """Build the Discord summary message from scored CSV rows."""
    counts = {rank: 0 for rank in "SABC"}
    for row in rows:
        counts[str(row["ランク"])] = counts.get(str(row["ランク"]), 0) + 1

    lines = [
        f"**リサーチ完了: {area} × {industry}**（全{len(rows)}件）",
        f"Sランク {counts['S']}件 / Aランク {counts['A']}件 / Bランク {counts['B']}件 / Cランク {counts['C']}件",
    ]
    top = [r for r in rows if r["ランク"] in ("S", "A")][:10]
    if top:
        lines.append("")
        lines.append("**優先度が高い店舗（上位）**")
        for row in top:
            lines.append(f"・[{row['ランク']}] {row['店名']}（{row['判定理由']}）")
    lines.append("")
    lines.append("詳細は添付のCSVを見てください。")
    return "\n".join(lines)
