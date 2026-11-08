# v1.1 review findings -> status in v1.2.0

Legend: **Fixed** (code + test) - **Mitigated** (reduced, not eliminated) - **Open** (deliberately left; see "Next").

| # | Finding | Status | Where |
|---|---|---|---|
| 1 | Standards don't drive the analysis | Fixed - rubric model; policies passed to AI | `analysis.evaluate_rubric`, `/api/rubric`, `docs/RUBRIC_MODEL.md` |
| 2 | Disabled rule still fires | Fixed | `test_disabled_criterion_is_really_skipped`, API test 12 |
| 3 | No user management / applicant role | Fixed | `/api/users`, role-scoped queries |
| 4 | Fragile amount extraction | Fixed (+ source line, officer confirm) | `ExtractionTests` |
| 5 | AI overwrote rule risks | Fixed | `build_result`, `test_ai_cannot_remove_rule_risks` |
| 6 | Evidence "supported" by keyword | Fixed (mentioned / negated / not mentioned) | `EvidenceNegationTests` |
| 7 | "Break-even" = expenses | Fixed (removed) | `test_demo_plan` |
| 8 | Float money, no validation | Mitigated - NUMERIC(18,2) columns, bounded request models | `Money`, `amount()` |
| 9 | Timezone display | Fixed | `utcnow`, `iso` |
| 10 | Two decision paths, no record | Fixed - single endpoint | API test 09 |
| 11 | No state machine / duties | Fixed | `DECISION_RULES`, API tests 09-10 |
| 12 | Stale DD / overwritten assessments | Fixed - versions, superseded questions | API test 06 |
| 13 | No AI run record | Fixed - model, prompt version, input hash | `AssessmentVersion` |
| 14 | Audit not tamper-evident / not atomic | Fixed - hash chain, single commit | API test 14 |
| 15 | Report buttons 401 | Fixed - authenticated fetch + blob | `openReport` |
| 16 | Postgres startup crash | Fixed (no raw SQL) - **verify in CI Postgres job** | `test_no_postgres_hostile_sql` |
| 17 | Event-loop blocking | Fixed - sync endpoint, 45 s AI timeout | `analyse_application_file` |
| 18 | Upload hardening, scanned PDFs | Mitigated - bounded read, magic bytes, zip guard, empty-text 422. No OCR, no malware scan | `validate_upload` |
| 19 | Default credentials / CORS `*` | Fixed | `test_no_default_credentials_anywhere` |
| 20 | Weak rate limiter | Mitigated - IP+user key, purge. Still per-process | `rate_ok` |
| 21 | AI data protection | Mitigated - opt-in, PII stripping. Needs your privacy review | `Institution.ai_enabled` |
| 22 | Prompt injection | Mitigated - fenced input, enums, quote verification | `AiHandlingTests` |
| 23 | Misc security | Mostly fixed - CSP, HSTS, non-root, token revocation. Tokens still in sessionStorage; dependencies range-pinned, not locked | |
| 24 | Layered single file | Fixed | `app.py` + `analysis.py` |
| 25 | No tests / thin CI | Fixed | `tests/`, `ci.yml` |
| 26 | Packaging drift | Fixed - one repo, `VERSION`, changelog | `test_single_version_source` |
| 27 | Dashboards load everything | Fixed - SQL aggregates, pagination | `/api/management/dashboard` |

## Next (not done in 1.2.0)
Alembic migrations - Redis-backed rate limiting and token blacklist - HttpOnly cookie sessions + CSRF - object storage for documents - OCR for scanned PDFs - malware scanning - rubric versioning (freeze per assessment) - lock file (`pip-compile`) after first green CI - PDF export - e-mail notifications - independent penetration test.
