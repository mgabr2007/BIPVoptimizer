# Research-integrity repair branch

Subsequent review repairs and current validation status: [PR1_REVIEW_FOLLOWUP.md](PR1_REVIEW_FOLLOWUP.md). The original validation record below describes the first repair commit.

Baseline: `00475a22d7248ee7f4ec6cc5bfbcac1d909b0a18` (main).
This is a development repair, not a production release or a scientific validation of the complete application.

## Changes

| Area | Change | Compatibility / numerical effect |
|---|---|---|
| Financial math | Shared pure functions for NPV, conventional IRR and cumulative simple payback. | `[-1000,600,600]` payback changes from 1 to 1.6666667 years. The utility's former average-return ratio is replaced by IRR. |
| IRR units / zero | Shared core returns a fraction; existing UI, report dictionaries and flat DB write use percent. Zero remains zero. | Newly written flat DB IRR is percent, matching the UI. Old stored rows are not migrated; check their original units before comparing. |
| IRR ambiguity | Non-conventional cash flows return unavailable instead of choosing an arbitrary root. | A negative later cash flow, e.g. replacement expenditure, can make IRR unavailable even if a unique root happens to exist. NPV and payback remain available. |
| Forecast claims | Removed fixed R², accuracy, cross-validation and feature-importance claims from the historical-data page and new scenario reports. | Existing trend/seasonal projection retained, labelled `trend-scenario-v2`, explicitly not evaluated. No RandomForest is introduced. |
| Forecast RNG | Local NumPy RandomState replaces global seeding. | Retains the legacy seeded projection sequence for valid inputs without changing other modules' RNG state. Invalid/missing consumption is rejected. |
| Optimizer | Pure testable weighted engine; zero/one candidate handling; deterministic seed 42; errors surface instead of becoming zero fitness. | Still weighted scalar search, not NSGA-II or a Pareto solver. Feasible masks are deduplicated and ranked. |
| Optimizer consistency | Reporting now uses the same Step 5 yield formula and maintenance rate as fitness. | Maintenance defaults to the explicitly passed legacy fitness assumption of 1.5%, replacing the report's conflicting 2.5%. Output values may change. |
| Feasibility | Minimum coverage rejects infeasible candidates rather than applying a soft penalty. | Infeasible scenarios may now produce no results, as required by the labelled minimum. |
| Solver persistence | Save seed/settings/method/version/fitness in existing `selection_details` JSON. Removed pre-run DELETE. | Existing successful results survive a solver failure; DB replacement remains transactional. This does not implement immutable run history. |
| Project selection | No latest-project or name-based fallback; no automatic first dropdown selection. | Users select a project explicitly. Conflicting IDs fail closed. This is not a full authorization system. |
| Financial session state | Cached financial outputs are scoped to project ID. | Switching projects does not reuse another project's financial result cache. Scenario/input fingerprinting still needs implementation. |
| Tariff adapter | Removed unfetched fixed prices and the wholesale-to-building-rate multiplier. | Adapter now returns unavailable; users must supply verified contract tariffs through Project Setup. It no longer invents a successful institutional response. |
| Report loading | Removed stray indented dictionary entries in `utils/report_data_extractor.py`. | Repairs a syntax error in a module imported by comprehensive reports. |

Scientific calculation references: [NumPy Financial IRR](https://numpy.org/numpy-financial/latest/irr.html) and [NPV timing](https://numpy.org/numpy-financial/latest/npv.html). These establish definitions, not application validation. Source-code defects and regression outputs are the primary evidence for this repair.

## Validation performed

Run from repository root:

```sh
python -m unittest discover -s tests -v
git diff --check
```

Local environment: Python 3.12 with available NumPy/Pandas; production configuration declares Python 3.11. No dependency pins or lockfile changed.

- 19 regression tests passed: hand-computable cash flows, invalid financial values, IRR unit compatibility, deterministic forecast metadata/RNG, zero/one-window optimization, exhaustive two-window weighted optimum, infeasible constraints, scoring/report agreement, explicit project selection, escaped scenario HTML and tariff availability semantics.
- All changed/new Python files parse successfully.
- Comprehensive report section renders with missing R² rather than formatting None as a number.
- `git diff --check` passes.
- A broader compile check identified an existing syntax error in `services/report_generator_old.py` near line 516. No Python caller of this legacy module was found in the source search. It is not repaired or silently removed by this branch.

Not performed: full Streamlit browser workflow, production DB operations, deployment, live weather/AI calls, dependency installation from the production lock, schema migration, or dissertation result reproduction. The local environment does not have the complete Streamlit/PostgreSQL application dependencies. Unit tests do not establish end-to-end compatibility.

## Remaining work before production release

1. Run the full workflow in a Replit development copy with a test PostgreSQL database and the locked Python 3.11 environment; test project creation/loading, navigation, invalid inputs, saves/reloads and exports. Verify all schema variants and nullable metric handling. The database manager contains duplicate method definitions; reconcile these against the live schema.
2. Audit the active Step 7 annual-only balance, savings, temporal aggregation and multi-year demand normalization. The alternative modular engine's nonconserving seasonal factors and fallback physics remain unrepaired because it is not the entry-point's active route. Do not interpret this branch as resolving all radiation/energy issues.
3. Reconcile forecast date/calendar handling, growth assumptions, partial-year data, schedule modifiers and long-term projection uncertainty. Seeded perturbation is preserved for reproducibility and disclosed; it is not a validated forecast interval. Historical totals can span multiple years; review annualization before using those values in finance.
4. Validate plane-of-array radiation, temperature, shading, active area, efficiency conventions and DC/AC losses against independent fixtures. The optimizer still uses the pre-existing yield approximation and normalization; this branch is not a new physical model.
5. Add user authorization and ownership filtering for every project list/load/write. Explicit project selection only removes accidental fallback. Complete cache invalidation for all upstream changes and scenario selection.
6. Introduce immutable run IDs, input hashes and model versions across all tables and reports before replacing research results. Existing application save routines overwrite project results. Back up/export historical data before testing repaired runs on a production project.
7. Complete report consolidation and an audit of old records/other report paths for unverified model claims, invented defaults and mixed IRR units. This branch does not modify historical database rows. Review remaining standards/benchmark assertions separately.
8. Replace unavailable tariff adapters with verified providers or explicitly sourced contract inputs. Review other rate modules independently; this patch covers `services/energy_price_api.py` and its existing API callers.
9. Verify financial cash flows distinguish self-consumption/export, O&M/replacements and degradation. Some finance paths still treat all PV generation as avoided imported electricity; the shared metric fixes do not repair that upstream assumption.

## Replit review and rollback

Check out the repair branch in a development copy; preserve any uncommitted Replit changes and do not reset them. Use a test database, run the regression suite, then execute the complete workflow. Compare new results to exported historical results and explain differences above. Keep this PR as a draft until those checks pass.

No production deployment, merge or database write was performed in preparing this branch. Roll back code by reverting the repair commit; do not rewrite branch history. Code rollback does not restore overwritten database rows: use a verified pre-release database backup if deployment testing later writes to production.
