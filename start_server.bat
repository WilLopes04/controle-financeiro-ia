@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

cd /d D:\ControleFinanceiro

call venv\Scripts\activate

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info >> D:\ControleFinanceiro\server.log 2>&1