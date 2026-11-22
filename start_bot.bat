@echo off
cd /d %~dp0
where python >nul 2>nul
if errorlevel 1 goto nopython
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
pip install -q -r requirements-bot.txt
if exist .env goto run
set /p TOKEN=Paste your Discord bot token and press Enter: 
echo DISCORD_TOKEN=%TOKEN%> .env
:run
echo Starting bot... Press Ctrl+C to stop.
python bot.py
pause
exit /b 0
:nopython
echo Python was not found on this PC.
echo Install it from https://www.python.org/downloads/
echo IMPORTANT: check "Add python.exe to PATH" during setup.
pause
