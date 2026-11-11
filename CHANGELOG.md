# Changelog

Version number lives in one place: the `VERSION` file. `backend/app.py` reads it; `/api/health`, reports and the Docker image all follow.

## 1.3.1 - 2026-11-11
- Phones: no empty band above pages; the menu closes by tapping outside it, with its x button, or with the phone's Back button.
- Releases now reach phones straight away: the page, styles and script are served with `Cache-Control: no-cache`, and the page asks for `styles.css` and `app.js` by version, so a browser can never pair a new page with an old stylesheet.

## 1.3.0 - 2026-11-08
CEDA Innovation Management Portal edition (hackathon prototype). Renamed to match the updated hackathon guidelines (10 Nov 2026). **Requires a fresh database** (new columns and tables).

### Product
- **Idea submission**: title, problem, solution, target users, sector and stage. Required for submitters; checked by the server, not just the form.
- **Reviewer assignment**: administrators assign evaluators to each idea. Evaluators only see ideas they are assigned to (or created).
- **Human scoring**: weighted 1-5 criteria configured by administrators. Evaluators score independently and never see each other's scores; adjudicators and administrators see the panel view with averages, spread and a disagreement flag.
- **Revise and resubmit**: submitters can edit their idea and upload a new version after it is sent back. Feedback written by evaluators and adjudicators is shown to the submitter.
- **Timeline** of every status change for each idea, plus a progress stepper.
- CEDA labels throughout: Submitter, Evaluator, Adjudicator, Administrator; Panel review, Revise and resubmit, Adjudication, Awarded, Declined.
- Submitters cannot upload while their idea is with the panel.

### Engineering
- New tables `score_criteria`, `review_assignments`, `review_scores`; new endpoints under `/api/applications/{id}/assignments|scores|idea|timeline` and `/api/score-criteria`.
- New API tests for assignment visibility, independent scoring, panel maths, mandatory idea fields, editing locks, resubmission and the timeline.

## 1.2.0 - 2026-10-03
Hardening and standards release following the v1.1 code review. **Requires a fresh database** (v1.1 and earlier held demo data only; the app refuses to start on an old schema rather than corrupt it).

### Product
- **Institution standards drive the analysis.** New per-institution / per-programme *rubric* (numeric, evidence and qualitative criteria, mandatory flags, weights). Risks, evidence gaps, due-diligence questions and the criteria-coverage indicator all come from it. Policy knowledge items are supplied to the AI as context.
- **User management** (admin creates officers, committee members, applicants), roles `admin / officer / committee / applicant`, applicants see only their own cases and never the assessment.
- **Workflow state machine** with separation of duties: officers analyse and refer; committee members approve or decline referred cases; nobody can decide a case they referred.
- **One decision endpoint** that writes the DecisionRecord (with the assessment version relied on), updates status, notifies and audits in one transaction.
- **Assessment versioning**: every upload or officer correction creates a new assessment version; due-diligence answers survive re-analysis; stale questions are marked superseded.
- Officers can **confirm or correct** revenue/expenses read from a document; the source line is shown next to each figure.
- AI runs record model, prompt version and input hash. Quotations returned by the AI are checked against the document.

### Fixes
- Financial extraction: years, percentages, `1.2 million`, `900k`, `1 200 000` and sentence-crossing matches handled; unknown is `None`, not `0`.
- Disabled rules really are disabled. AI can no longer replace rule-based risks. "Mentioned" is no longer reported as "supported"; negations ("no quotations") are detected.
- Removed the mislabelled `break_even` metric (it was just expenses).
- Postgres startup crash (`institution_id=""`) removed together with the hand-rolled SQLite migration.
- Committee report buttons now work (fetched with the auth header, not `window.open`). Reports are built in memory, not written to a shared folder.
- Timestamps are UTC with `Z` and display in local time.
- Upload: bounded read, magic-byte check, DOCX zip-bomb guard, empty-text detection (scanned PDFs), analysis runs in a worker thread.
- Audit log is hash-chained, written in the same transaction as the action, and verifiable at `/api/audit/verify`.

### Security
- No default passwords or secrets; production refuses to start without `JWT_SECRET` (32+) and `ADMIN_PASSWORD` (12+). Login form no longer pre-filled.
- Login rate limit keyed by IP + username (cannot lock out admin from elsewhere); stale keys purged.
- Tokens revocable (`token_version`), sessionStorage instead of localStorage, strict CSP (no inline script), HSTS in production, container runs as non-root.
- AI is **opt-in per institution**, strips e-mails/phone numbers, fences the plan text as untrusted input, validates enums.

### Engineering
- Backend rewritten as one coherent module (no per-version layers or route patching); pure logic in `backend/analysis.py`.
- 46 unit tests (analysis), ~20 end-to-end API tests, repo-consistency tests; CI runs them on SQLite **and** PostgreSQL, then builds and smoke-tests the container.

## 1.1.0 and earlier
Pilot prototypes (see the Master package). Superseded by 1.2.0.
