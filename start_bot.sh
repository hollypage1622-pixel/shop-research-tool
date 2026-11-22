#!/bin/bash
cd "$(dirname "$0")"
command -v python3 >/dev/null 2>&1 || { echo "Python3が必要です。https://www.python.org/downloads/ からインストールしてください。"; exit 1; }
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements-bot.txt
if [ ! -f .env ]; then
  read -p "Discord botのトークンを貼ってEnter: " T
  echo "DISCORD_TOKEN=$T" > .env
fi
echo "botを起動します。止めるときは Ctrl+C を押してください。"
python bot.py
