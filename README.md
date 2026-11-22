# shop-research-tool

地域 × 業種を指定するだけで、実店舗を自動収集し、各店のホームページの状態をチェックして **営業優先度スコア付きのCSV** を出力するCLIツールです。

「HPがない店」「無料ビルダーのまま放置されている店」「スマホ対応していない店」を自動で洗い出せるため、Web制作の営業リスト作成や、地域ビジネスの市場調査に使えます。

## 特徴

- **APIキー不要**：店舗データは OpenStreetMap（Nominatim / Overpass API）から取得。cloneしてすぐ動きます
- **依存ライブラリゼロ**：Python標準ライブラリのみで実装（urllib / re / csv）
- **HPの状態を自動判定**：到達可否、スマホ対応（viewport有無）、無料ビルダー検出（Jimdo / Wix / Ameba Ownd / ペライチ等）、HTTPS、SNSリンク、電話発信リンク、更新の古さ
- **営業優先度スコアリング**：Web集客の弱さをもとに 0〜100 点と S/A/B/C ランクを算出し、理由も明記
- **入力CSVモード**：手持ちの店名・URLリストを直接チェックすることも可能

## 使い方

```bash
# 検索モード：札幌市中央区のカフェを半径1.5kmで最大30件
python -m shop_research --area "札幌市中央区" --industry カフェ

# 半径と件数を指定
python -m shop_research --area "大阪市北区" --industry 美容室 --radius 2000 --limit 50

# 入力モード：店名,URL のCSVをチェック
python -m shop_research --input my_shops.csv --output result.csv
```

対応業種プリセット：美容室 / カフェ / 飲食店 / 居酒屋 / パン屋 / 花屋 / 整体・マッサージ / 歯科 / 自動車整備 / ペット / 学習塾 / 不動産（`shop_research/sources.py` の `INDUSTRY_PRESETS` に追加可能）

## 出力サンプル

実際に「札幌市中央区 × カフェ」で実行した結果（抜粋）:

| 店名 | HP | スマホ対応 | スコア | ランク | 判定理由 |
|---|---|---|---|---|---|
| Café 倫敦館 | なし | - | 90 | S | ホームページなし |
| ドトールコーヒーショップ | あり | × | 20 | B | スマホ非対応の可能性（viewportなし） |
| アトリエ・モリヒコ | あり | ○ | 5 | C | 電話発信リンクなし |
| オニヤンマ コーヒー＆ビア | あり | ○ | 0 | C | 大きな課題なし |

全カラムの出力は [examples/sample_output.csv](examples/sample_output.csv) を参照。

## スコアリングの考え方

「新しいホームページで得られる改善幅が大きい店」ほど高スコアになります。

| 条件 | 加点 |
|---|---|
| ホームページなし | 90点（即Sランク） |
| サイトに接続できない | +40 |
| 無料ビルダー利用 | +25 |
| スマホ非対応の可能性（viewportなし） | +20 |
| HTTPS未対応 | +10 |
| 更新が古い可能性（©表記が3年以上前） | +10 |
| 電話発信リンクなし | +5 |

ランク：S = 60点〜 / A = 35点〜 / B = 15点〜 / C = それ以下

## Discord botとして使う

Discordで `!リサーチ 札幌市中央区 カフェ` と送ると、botがリサーチを実行して、要約メッセージとCSVファイルをそのチャンネルに返します。

```
!リサーチ <エリア> <業種> [件数]
!ヘルプ
```

セットアップ:

1. [Discord Developer Portal](https://discord.com/developers/applications) で Application を作成し、Bot を追加してトークンを取得
2. Bot設定で **Message Content Intent** を有効化
3. OAuth2 → URL Generator で scope `bot`、権限（メッセージ送信 / ファイル添付 / メッセージ履歴の閲覧）を選んで招待URLを発行し、自分のサーバーに招待
4. このリポジトリで:

```bash
pip install -r requirements-bot.txt
cp .env.example .env   # DISCORD_TOKEN にトークンを記入（.envはgit管理外）
python bot.py
```

本体（CLI）は標準ライブラリのみのまま、Discord連携は `bot.py` と `shop_research/discord_logic.py`（コマンド解析・整形、テスト済み）に分離しています。

## テスト

```bash
python -m unittest discover -s tests
```

判定ロジック（無料ビルダー検出、HTMLシグナル抽出、スコアリング）のユニットテストを用意しています。

## 注意事項・制限

- 店舗データはOpenStreetMapの登録状況に依存します。住所が番地まで入っていない店舗や、未登録の店舗は拾えません
- 到達可否は実行環境のネットワークに影響されます。大手チェーン等はbot対策で接続を弾く場合があり、その場合は理由欄に記録されます
- スマホ対応・更新時期はHTMLからのヒューリスティクス判定です。最終確認は目視を推奨します
- OpenStreetMapの利用ポリシーに従い、リクエスト間隔は控えめに設定しています（`--delay` で調整可能）
- 収集した情報の利用は各サービスの規約と法令の範囲内で行ってください

## ライセンス

MIT
