@echo off
echo Iniciando Compliance Suite...
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python app.py
pause
