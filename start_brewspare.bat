@echo off
start "BrewSpare Backend" cmd /k "cd /d %~dp0backend && if not exist .venv python -m venv .venv && call .venv\Scripts\activate && pip install -r requirements.txt && python -m app.seed && uvicorn app.main:app --reload --port 8000"
start "BrewSpare Frontend" cmd /k "cd /d %~dp0frontend && if not exist node_modules npm install && if not exist .env.local copy .env.local.example .env.local && npm run dev"
