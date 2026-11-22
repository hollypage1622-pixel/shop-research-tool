"""CLI: search shops in an area, check their websites, export a scored CSV.

Usage:
    python -m shop_research --area "札幌市中央区" --industry カフェ
    python -m shop_research --input my_shops.csv   # 店名,URL のCSVを直接チェック
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

from .checker import check_site
from .scoring import score_lead
from .sources import INDUSTRY_PRESETS, search_shops

CSV_COLUMNS = [
    "店名", "住所", "電話番号", "HP", "到達可否", "スマホ対応", "無料ビルダー",
    "HTTPS", "SNS", "電話リンク", "最終更新の目安", "優先度スコア", "ランク", "判定理由",
]


def build_row(name: str, address: str, phone: str, website: str) -> dict:
    has_site = bool(website)
    check = check_site(website) if has_site else None
    scored = score_lead(has_site, check)
    if check is None:
        return {
            "店名": name, "住所": address, "電話番号": phone, "HP": "",
            "到達可否": "-", "スマホ対応": "-", "無料ビルダー": "-",
            "HTTPS": "-", "SNS": "-", "電話リンク": "-",
            "最終更新の目安": "-", "優先度スコア": scored.score,
            "ランク": scored.rank, "判定理由": " / ".join(scored.reasons),
        }
    return {
        "店名": name,
        "住所": address,
        "電話番号": phone,
        "HP": website,
        "到達可否": "OK" if check.reachable else "NG",
        "スマホ対応": "○" if check.has_viewport else "×",
        "無料ビルダー": check.free_builder or "-",
        "HTTPS": "○" if check.is_https else "×",
        "SNS": ",".join(check.sns) or "-",
        "電話リンク": "○" if check.has_tel_link else "×",
        "最終更新の目安": str(check.copyright_year or check.last_modified or "-"),
        "優先度スコア": scored.score,
        "ランク": scored.rank,
        "判定理由": " / ".join(scored.reasons) or "大きな課題なし",
    }


def write_csv(rows: list[dict], out_path: Path) -> None:
    rows.sort(key=lambda r: (-int(r["優先度スコア"]), r["店名"]))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="shop-research",
        description="地域×業種で店舗を集め、HPの状態を自動チェックして営業優先度つきCSVを出力します。",
    )
    parser.add_argument("--area", help='検索エリア（例: "札幌市中央区"）')
    parser.add_argument(
        "--industry",
        help=f"業種プリセット（対応: {', '.join(INDUSTRY_PRESETS)}）",
    )
    parser.add_argument("--radius", type=int, default=1500, help="検索半径メートル（既定 1500）")
    parser.add_argument("--limit", type=int, default=30, help="最大件数（既定 30）")
    parser.add_argument("--input", help="店名,URL列を持つCSVを直接チェックするモード")
    parser.add_argument("--output", default="shops.csv", help="出力CSVパス（既定 shops.csv）")
    parser.add_argument("--delay", type=float, default=1.0, help="サイト確認の間隔秒（既定 1.0）")
    args = parser.parse_args(argv)

    targets: list[tuple[str, str, str, str]] = []  # name, address, phone, website
    if args.input:
        with open(args.input, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                targets.append(
                    (row.get("店名", ""), row.get("住所", ""), row.get("電話番号", ""), row.get("URL", row.get("HP", "")))
                )
    elif args.area and args.industry:
        print(f"検索中: {args.area} / {args.industry}（半径{args.radius}m）...", file=sys.stderr)
        shops = search_shops(args.area, args.industry, args.radius, args.limit)
        targets = [(s.name, s.address, s.phone, s.website) for s in shops]
        print(f"{len(targets)}件の店舗が見つかりました。サイトを確認します...", file=sys.stderr)
    else:
        parser.error("--area と --industry、または --input のどちらかを指定してください")

    rows = []
    for i, (name, address, phone, website) in enumerate(targets, 1):
        print(f"[{i}/{len(targets)}] {name}", file=sys.stderr)
        rows.append(build_row(name, address, phone, website))
        if website and args.delay:
            time.sleep(args.delay)

    out = Path(args.output)
    write_csv(rows, out)
    s_count = sum(1 for r in rows if r["ランク"] == "S")
    a_count = sum(1 for r in rows if r["ランク"] == "A")
    print(f"完了: {out}（全{len(rows)}件 / Sランク{s_count}件 / Aランク{a_count}件）", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
