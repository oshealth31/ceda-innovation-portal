# Rubric data model (institution standards)

A **criterion** is one standard the institution checks on every assessment. Table `rubric_criteria`.

| Field | Meaning |
|---|---|
| `institution_id` | Tenant. |
| `programme_id` | `NULL` = applies to all programmes. A programme-specific criterion with the same `key` overrides the institution-wide one. |
| `key`, `label`, `description` | Stable identifier, display name, what "good" looks like (also shown to the AI for qualitative criteria). |
| `kind` | `numeric`, `evidence` or `qualitative`. |
| `metric`, `comparator`, `threshold` | Numeric only. Metrics: `revenue, expenses, profit, margin, expense_to_revenue_ratio, funding, contribution, funding_to_contribution, owner_contribution_pct`. Comparators: `>= <= > <`. |
| `keywords_json` | Evidence only. Phrases looked for in the document, with same-sentence negation detection. |
| `mandatory` | A failed or unassessable mandatory criterion is surfaced as a banner and, for evidence, as a high risk. |
| `weight` | Share of the *criteria-coverage* indicator. Qualitative criteria have weight 0 (officer judgement). |
| `enabled` | Disabled criteria are skipped entirely. |

## Result per criterion
`status`: `pass | fail` (numeric), `mentioned | negated | not_mentioned` (evidence), `unknown` (figure unavailable), `needs_review` (qualitative). Plus `detail`, `observed`, optional AI note with a verified/unverified quotation.

## Scoring
`coverage_pct = weighted share of assessable criteria that are met`. It is an **indicator of completeness for the officer, not a recommendation**; unassessable criteria are excluded and counted separately.

## Why this shape
- Numeric rules are code, so results are reproducible and explainable.
- Evidence rules only claim "mentioned" - proof is a human act (`claim_evidence`).
- Qualitative criteria give the AI a bounded question to comment on and a human the final say.
- Each assessment version stores the full per-criterion result, so a decision can always be traced to what the officer saw.

## Next steps
Per-programme templates, criterion groups/sections, document-type requirements (e.g. "quotation must be a separate file"), and rubric versioning (freeze the rubric used for each assessment).
