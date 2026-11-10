# CEDA Innovation Management Portal (FundingLens AI v1.3.0)

Prototype for the CEDA Innovation Management Portal Hackathon (9-12 November 2026), built on the FundingLens AI platform.

## CEDA demo in 6 steps
1. **Submitter** (`applicant1`) submits an idea: required fields, then an idea document.
2. **Administrator** (`admin`) assigns one or more **Evaluators** (`officer1`) under *Evaluators* on the idea page.
3. **Evaluators** score each criterion 1-5, independently. They can *Send back for revision* with feedback.
4. **Submitter** sees the feedback in the timeline, edits the idea and uploads a revised document.
5. **Evaluator** refers the idea to adjudication. The **Adjudicator** (`committee1`) sees the panel scores and awards or declines.
6. **Administrator** shows the dashboard, scoring criteria and the tamper-evident audit trail.

Role mapping in code: `applicant` = Submitter, `officer` = Evaluator, `committee` = Adjudicator, `admin` = Administrator.

---

# FundingLens AI platform notes

Decision-support platform that helps funding institutions receive business plans and review them against **their own standards**. AI is advisory: numbers are computed by deterministic code, every figure shows its source, and only authorised humans decide.

## What it does
1. Applicant (or officer) creates an application and uploads a business plan (PDF, DOCX, TXT, MD, CSV).
2. The platform extracts figures, evaluates the institution's **rubric** (numeric thresholds, evidence checklists, officer-judged criteria), lists risks and evidence gaps, and generates due-diligence questions.
3. Optional AI commentary (opt-in per institution) adds a summary and notes - quotations are verified against the document.
4. Officer confirms figures, answers due diligence, refers to committee. A *different* committee member approves or declines. Everything is audited in a tamper-evident log.
5. Committee report as HTML or Word.

Roles: `admin`, `officer`, `committee`, `applicant`.

## Run locally (no Docker)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export ENVIRONMENT=development SEED_DEMO=true DEMO_PASSWORD='choose-a-demo-password'
uvicorn backend.app:app --reload        # http://127.0.0.1:8000
```
In development an admin password is generated and printed in the log if `ADMIN_PASSWORD` is unset. Demo logins: `officer1`, `committee1`, `applicant1` with `DEMO_PASSWORD`.

## Run with Docker Compose (PostgreSQL)
```bash
cp .env.example .env     # fill JWT_SECRET, ADMIN_PASSWORD, POSTGRES_PASSWORD (and DEMO_* for a demo)
docker compose up --build
```

## Tests
```bash
python -m unittest discover -s tests -v                       # unit + API (SQLite)
TEST_DATABASE_URL=postgresql://u:p@localhost/db python -m unittest tests.test_api -v
```

## Deploying the demo
Follow `docs/GITHUB_DEPLOY_CHECKLIST.md` (GitHub -> CI -> Render, about 45 minutes).

## Layout
`backend/analysis.py` pure logic (unit-tested) - `backend/app.py` API - `frontend/` portal - `tests/` - `scripts/smoke_test.py` post-deploy check - `docs/` checklist, review findings, rubric model.

## Governance
AI analysis is advisory and must not approve, decline, rank or recommend funding. Extracted figures must be confirmed by an officer. Keyword matches are never treated as verified evidence. Separate the person who refers a case from the person who decides it.
