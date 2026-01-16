# Repository Guidelines

## Project Structure & Module Organization

- `frontend/`: Next.js 14 + TypeScript + Tailwind (App Router lives in `frontend/app/`; shared UI in `frontend/components/`).
- `backend/`: FastAPI + Python (API routes in `backend/app/api/v1/`; data models in `backend/app/models/`; business logic in `backend/app/services/`).
- Supporting folders: `docs/`, `deploy/`, `docker/`, `scripts/`.

## Build, Test, and Development Commands

Prefer the top-level `Makefile`:

- `make setup` — install dependencies, initialize the local SQLite DB, and create `.env` from `.env.example` if missing.
- `make dev` — run frontend (http://localhost:3000) and backend (http://localhost:8000) in parallel.
- `make test` / `make lint` / `make format` — run tests, linters, and auto-formatters for both apps.
- `make db-reset` — delete and recreate the local dev DB.

Direct commands (when working in one app only):

- `cd backend && uvicorn app.main:app --reload --port 8000`
- `cd frontend && npm run dev`

## Coding Style & Naming Conventions

- Python: 4-space indentation; format/lint with Ruff (`backend/ruff.toml`, line length 100). Keep FastAPI routes thin and put logic in `services/`.
- TypeScript/React: format with Prettier (`frontend`: `npm run format`); lint with `next lint`. Components use `PascalCase.tsx` (e.g., `frontend/components/panels/ClaimsPanel.tsx`); hooks use `useX.ts` (e.g., `frontend/hooks/useDocument.ts`).

## Testing Guidelines

- Backend: `pytest` in `backend/tests/` (coverage enabled via `pytest-cov`). Add tests for new endpoints and service logic.
- Frontend: unit tests via Vitest (`npm test`) and e2e via Playwright (`npm run test:e2e`) for critical flows.

## Commit & Pull Request Guidelines

- Commits: short, imperative, sentence-case summaries (matches existing history). Keep unrelated changes split.
- PRs: include problem/solution summary, testing notes (`make test`/`make lint`), and screenshots/GIFs for UI changes. Call out env var or schema changes and update `README.md`/`DEPLOY.md` when applicable.

## Security & Configuration Tips

- Store secrets in `.env` (never commit it). LLM features require `ANTHROPIC_API_KEY`.
- Local DB defaults to SQLite (see `DATABASE_URL` in `.env.example`); use `make db-reset` if the schema/data gets out of sync.
