@echo off
chcp 65001 >nul
cd /d %~dp0
where python >nul 2>nul
if errorlevel 1 (
  echo Pythonが見つかりませんでした。
  echo https://www.python.org/downloads/ からインストールしてください。
  echo ※ インストール時に「Add python.exe to PATH」に必ずチェックを入れてください。
  pause
  exit /b 1
)
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
pip install -q -r requirements-bot.txt
if exist .env goto run
set /p TOKEN="Discord botのトークンを貼ってEnter: "
echo DISCORD_TOKEN=%TOKEN%> .env
:run
echo botを起動します。止めるときは Ctrl+C を押してください。
python bot.py
pause
