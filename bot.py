"""Discord bot entry point for shop-research-tool.

Setup:
    pip install -r requirements-bot.txt
    cp .env.example .env   # then put your bot token in .env
    python bot.py

In Discord:  !リサーチ 札幌市中央区 カフェ
The bot runs the research and posts a summary + the scored CSV.

Requires the "Message Content Intent" to be enabled in the
Discord Developer Portal (Bot settings).
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

import discord

from shop_research.cli import build_row, write_csv
from shop_research.discord_logic import (
    format_summary,
    help_text,
    is_help,
    parse_command,
)
from shop_research.sources import search_shops


def load_token() -> str:
    token = os.environ.get("DISCORD_TOKEN", "").strip()
    if token:
        return token
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("DISCORD_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DISCORD_TOKEN が未設定です。.env.example を参考に .env を作ってください。")


def run_research(area: str, industry: str, limit: int) -> tuple[list[dict], Path]:
    shops = search_shops(area, industry, radius_m=1500, limit=limit)
    rows = [
        build_row(s.name, s.address, s.phone, s.website) for s in shops
    ]
    out = Path(tempfile.gettempdir()) / f"research_{area}_{industry}.csv"
    write_csv(rows, out)
    return rows, out


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
_running = False


@client.event
async def on_ready() -> None:
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message: discord.Message) -> None:
    global _running
    if message.author.bot:
        return

    if is_help(message.content):
        await message.channel.send(help_text())
        return

    try:
        request = parse_command(message.content)
    except ValueError as exc:
        await message.channel.send(str(exc))
        return
    if request is None:
        return

    if _running:
        await message.channel.send("いま別のリサーチを実行中です。終わってからまたお願いします。")
        return

    _running = True
    try:
        await message.channel.send(
            f"リサーチ開始: {request.area} × {request.industry}（最大{request.limit}件）。数分かかります…"
        )
        rows, csv_path = await asyncio.to_thread(
            run_research, request.area, request.industry, request.limit
        )
        if not rows:
            await message.channel.send("店舗が見つかりませんでした。エリアや半径を変えて試してください。")
            return
        summary = format_summary(request.area, request.industry, rows)
        await message.channel.send(summary, file=discord.File(str(csv_path)))
    except Exception as exc:  # keep the bot alive on any research failure
        await message.channel.send(f"エラーが発生しました: {exc}")
    finally:
        _running = False


if __name__ == "__main__":
    client.run(load_token())
