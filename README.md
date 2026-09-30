<<<<<<< HEAD
# BrewSpare

BrewSpare is a local-first brewery maintenance and spare-parts planning website. It connects machine condition, maintenance history, spare-part demand, supplier lead time, inventory carrying cost, and procurement timing into one decision-support workflow.

## Target device
Designed for the supplied Windows x64 laptop:
- Intel Core Ultra 7 155H
- 32 GB RAM
- Intel Arc integrated graphics
- ~675 GB free storage

No dedicated GPU is required.

## Architecture
- Frontend: Next.js + React + TypeScript
- Backend: FastAPI + SQLAlchemy
- Database: SQLite by default for one-command local demo; PostgreSQL is supported through `DATABASE_URL`
- Analytics: deterministic demand forecast, maintenance-risk logic, availability planning, scenario analysis

## Quick start on Windows

### 1. Backend
Open PowerShell in `backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

Backend: http://localhost:8000
API docs: http://localhost:8000/docs

### 2. Frontend
Open a second PowerShell window in `frontend`:

```powershell
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

Website: http://localhost:3000

## Optional PostgreSQL
The app defaults to SQLite so it starts immediately on one laptop. To use PostgreSQL, create a database and set:

```env
DATABASE_URL=postgresql+psycopg://brewspare:brewspare@localhost:5432/brewspare
```

Then rerun `python -m app.seed`.

## Main user journeys
1. Plant Command Center → select FL-01 Bottle Filler → review risk and required parts.
2. FL-01 → SP-010 Filler Valve Seal Kit → see future-availability gap and procurement timing.
3. Procurement Planner → create a local approval/planning record. No external purchase is claimed.
4. Inventory → identify SP-015 as slow-moving/excess inventory and review carrying-cost exposure.
5. Scenario Simulator → model supplier delay and production increase.

## Demo data
All plant, financial, maintenance and sensor values are synthetic and intended for product demonstration only.
=======
# BrewSpare-hack
>>>>>>> 09c19deeeb7cbfcbb579f620fe98b369c54197bf
