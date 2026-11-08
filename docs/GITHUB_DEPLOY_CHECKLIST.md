# GitHub -> CI -> Demo deployment checklist

Tick each box in order. Paste this file into a GitHub Issue ("New issue" > paste) and GitHub turns the boxes into a trackable checklist.
Target: a live demo URL with three demo logins, reached through a green CI run. Allow about 45 minutes.

> **Read this first.** The API tests in `tests/test_api.py` and the Docker/Postgres path were written without being able to run the server where this package was prepared. **Your first CI run (Phase 3) is the first real execution.** Expect to fix a small number of issues there - Phase 3 tells you how.

---

## Phase 0 - Prepare (on your computer)
- [ ] Unzip the package; the folder should contain `backend/`, `frontend/`, `tests/`, `VERSION`, `Dockerfile`, `render.yaml`.
- [ ] Install Git and (optional) Python 3.12. Confirm: `git --version`
- [ ] Optional local check: `pip install -r requirements-dev.txt && python -m unittest discover -s tests -v`  (all green = skip surprises in Phase 3)
- [ ] Generate and **save in your password manager** (never in the repo):
  - [ ] `ADMIN_PASSWORD` - 12+ characters
  - [ ] `DEMO_PASSWORD` - 12+ characters, shared by `officer1`, `committee1`, `applicant1`
  - (`JWT_SECRET` is generated automatically by Render.)

## Phase 1 - Create the repository
- [ ] github.com > **New repository** > name `fundinglens-ai` > **Private** > do **not** add a README/.gitignore/licence.
- [ ] In the project folder:
  ```bash
  git init -b main
  git add .
  git status            # confirm .env and data/ are NOT listed
  git commit -m "FundingLens AI v1.2.0"
  git remote add origin https://github.com/<you>/fundinglens-ai.git
  git push -u origin main
  ```
- [ ] Open the repo on GitHub: you should see `README.md`, `VERSION`, `.github/workflows`.
- [ ] In `Dockerfile`, replace `OWNER/REPO` in the `org.opencontainers.image.source` label with your repo path; commit and push.

## Phase 2 - GitHub settings
- [ ] Settings > Actions > General > *Allow all actions and reusable workflows* (or allow the `actions/*`, `docker/*` ones).
- [ ] Settings > Actions > General > Workflow permissions: *Read repository contents* (the publish workflow requests `packages: write` itself).
- [ ] Settings > Code security: enable **Dependabot alerts** and **secret scanning** (free for private repos on most plans; skip if your plan lacks them).

## Phase 3 - First CI run (the important one)
- [ ] Actions tab > workflow **CI** > open the run triggered by your push.
- [ ] Job `test`, step *Compile*: green.
- [ ] Step *Unit + API tests (SQLite)*: green.
- [ ] Step *API tests against PostgreSQL*: green. (This is the check that v1.1's Postgres crash is gone.)
- [ ] Job `container`, step *Run container and smoke-test it*: green (prints `ALL CHECKS PASSED`).
- [ ] **If something is red:** open the failing step, copy the first traceback + the test name, fix, then
  `git add -A && git commit -m "fix: ..." && git push` and repeat. Typical first-run suspects:
  | Symptom | Likely cause / fix |
  |---|---|
  | `ImportError` / `ModuleNotFoundError` | A dependency range in `requirements.txt` resolved to a new major version - pin the previous one. |
  | A single `test_api` assertion fails | Read the assertion message; it names the rule being tested (e.g. separation of duties). Fix code or test, not both blindly. |
  | Postgres-only failure | Compare the SQL error with the SQLite run; usually a type or `GROUP BY` difference. |
  | Container job: connection refused | `docker logs fl` is printed automatically - look for a startup `RuntimeError` (missing secret) or a traceback. |
- [ ] Green on `main`. Note the commit SHA: `________`

## Phase 4 - Protect main
- [ ] Settings > Branches > **Add branch ruleset** (or classic rule) for `main`: require a pull request, require status checks **test** and **container**, block force pushes.
- [ ] From now on: work on a branch, open a PR, merge only when CI is green.

## Phase 5 - Container image (optional but recommended)
- [ ] Actions > **Publish container** ran on the push to `main` (or run it via *Run workflow*).
- [ ] Repo > Packages: image `ghcr.io/<you>/fundinglens-ai` with tags `latest` and `sha-...`.
- [ ] Tag a release: `git tag v1.2.0 && git push --tags` (adds a `1.2.0` image tag). Keep the git tag equal to the `VERSION` file.

## Phase 6 - Deploy the demo on Render
- [ ] Create a Render account; connect GitHub and grant access to the repo.
- [ ] Render dashboard > **New** > **Blueprint** > select the repo. It reads `render.yaml` (web service `fundinglens-demo` + Postgres `fundinglens-db`).
- [ ] When prompted, enter `ADMIN_PASSWORD` and `DEMO_PASSWORD` (from Phase 0). Leave everything else.
- [ ] Wait for the first deploy (5-10 min). Service page shows **Live**; note the URL: `https://________.onrender.com`
- [ ] Service > Settings: confirm **Auto-Deploy** is "After CI checks pass" (set by the blueprint) so only green commits deploy.
- [ ] Service > Environment: confirm there is **no** `OPENAI_API_KEY` yet (the demo runs fine without AI).

## Phase 7 - Smoke test the live demo
- [ ] From your computer:
  ```bash
  python scripts/smoke_test.py https://<your-service>.onrender.com officer1 '<DEMO_PASSWORD>' committee1
  ```
  Expect `ALL CHECKS PASSED` (the first request may take ~1 minute while the free instance wakes).
- [ ] Open the URL in a browser. The login page must show **empty** username/password fields.
- [ ] Sign in as `admin`: **Settings** > change the password to a new one only you know. (Everyone else is signed out automatically.)

## Phase 8 - Rehearse the demo script (10 minutes)
- [ ] **Applicant** (`applicant1`): *New Application* > create "Demo Bakery", funding 300000, contribution 60000, programme SME Growth > upload `demo_data/business_plan_demo.txt` > see "document received" and no assessment (applicants never see it).
- [ ] **Officer** (`officer1`): Applications > open "Demo Bakery". Show: figures with their *source line* and the "unconfirmed" warning > **Confirm figures** (creates assessment v2) > rubric table (mandatory banner, "mentioned" is not "verified") > answer one due-diligence question > upload a second file and show the answer survives and versions appear > **Refer to committee** with a rationale.
- [ ] **Committee** (`committee1`): Committee Queue > open case > **Record approval** with rationale. Open **View committee report** and **Download Word report**.
- [ ] Try to approve as `officer1` / as the same person who referred: show it is refused (separation of duties).
- [ ] **Admin**: Audit Trail > **Verify integrity** (chain intact) > Standards: change the margin threshold or disable a criterion, upload again, show the result changes - "your standards drive the analysis".
- [ ] Management Dashboard: pilot KPIs.

## Phase 9 - Know the demo limits (tell your audience)
- [ ] Free Render web services sleep when idle and wake slowly; open the URL 2 minutes before a live demo.
- [ ] The free container disk is **ephemeral**: uploaded files vanish on restart/redeploy while database rows stay. Consequence: *Confirm figures* on a case whose file was lost answers "upload it again". Fine for a demo; use object storage (S3-compatible) or a persistent disk for a pilot.
- [ ] Check Render's current free Postgres terms (expiry/size) before relying on it for more than a demo - the published spec page does not state them.
- [ ] Demo data only. No real applicant data until: independent security test, privacy review (data-protection law, AI provider terms), backups, HTTPS custom domain, SSO decision.

## Phase 10 - Optional: switch on AI commentary
- [ ] Render service > Environment: add `OPENAI_API_KEY` and `OPENAI_MODEL` (a model your account can use). Save (redeploys).
- [ ] Sign in as `admin` > Settings > tick **Allow AI assistance**. (Off by default per institution.)
- [ ] Upload a plan: the review page banner says `mode: llm`, and risks show "quote verified / not found" badges. If AI fails you silently get rules-only results (banner says why).

## Rollback and troubleshooting
| Problem | Action |
|---|---|
| Bad deploy | Render > service > **Events/Deploys** > roll back to the previous deploy. Or `git revert <sha> && git push`. |
| App won't start: "JWT_SECRET must be..." / "ADMIN_PASSWORD must be..." | Env var missing or too short (Render > Environment). |
| App won't start: "created by an older FundingLens release" | Database holds a v1.1 schema. Use a fresh database (demo data only). |
| Logins say "Too many attempts" | Wait 5 minutes (per IP + username). |
| Report window blank | Allow pop-ups for the demo site. |
| Forgot admin password | Render > `fundinglens-db` > connect (psql) > `DELETE FROM users WHERE username='admin';` then restart the service. On start it recreates `admin` from the `ADMIN_PASSWORD` env var. (Audit rows keep their history.) |

## Done when
- [ ] CI green on `main` - [ ] live URL passes `smoke_test.py` - [ ] admin password changed - [ ] demo script rehearsed once end-to-end
