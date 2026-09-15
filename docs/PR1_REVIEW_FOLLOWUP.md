# PR #1 review follow-up

> Historical record of the first repair. The subsequent multi-user implementation, NSGA-II comparison, immutable evidence and measured research studies supersede several remaining-work items below. See [current setup and validation scope](MULTIUSER_RESEARCH_SETUP.md).

This extends commit `597e2ade88994a574b87032f40815241efc6be4c`. It remains an experimental repair, not a validated research release. No production database migration, data rewrite, merge or deployment is part of this change.

## Implemented

- Step 6 and optimizer scoring/report normalization use the same active BIPV area, explicit fractional efficiency and required annual radiation. Missing irradiation no longer gets 1000 kWh/m²/year in the active Step 6 calculation. Old ambiguous specifications must be regenerated in a development/test project.
- Weighted fitness order survives the page and database handoff to Step 9. First-year ROI remains a separate metric, not a substituted ranking or IRR.
- Annual demand uses the most recent 12 consecutive dated monthly observations. Missing dates, duplicates, gaps, unordered months and partial-year series are rejected instead of silently annualized. Step 7/8 recalculate the reference from observations rather than trusting old multi-year `annual_consumption` totals.
- Scenario seasonality uses the latest reference year and its actual calendar months. A zero older year no longer causes division by zero when the latest year is valid. The legacy trend/growth assumptions and seeded perturbation remain unevaluated; perturbations are not confidence intervals.
- Steps 7–9 explicitly use an **annual-netting scenario**. Benefit is `min(generation, demand)*import_tariff + max(generation-demand, 0)*export_tariff`. This is not time-matched self-consumption. A zero export tariff is an explicit no-export-revenue assumption. Annual demand is constant across financial years; both tariffs share the selected escalation. For export tariffs no greater than import tariffs, this annual-netted revenue is an upper bound on time-matched no-storage revenue with identical annual totals and no curtailment.
- Step 9 applies degradation to yearly generation, and includes O&M, inverter replacement, tax credit and rebate in one cash-flow calculation. Summary/CSV first-year net benefit comes from that cash flow. The capital/energy shortcut is no longer labelled LCOE, and the invented 10,000 kWh independence denominator is removed.
- One checked financial transaction replaces the prior repeated saves. A project row lock serializes financial writers. Failed saves do not display completion. NULL payback and IRR stay unavailable; known zero IRR remains zero. Legacy IRR units without metadata are withheld, not guessed or migrated.
- Financial detail JSON now stores `{rows, metadata}`. The loader also accepts legacy row lists and either TEXT or decoded JSON. Metadata includes model version, percent IRR units, input fingerprint, scenario method, selected solution and assumptions. Existing cash-flow readers in this repository go through this loader.
- Optimizations carry an upstream-input fingerprint. Step 9 refuses stale or unversioned optimization inputs; financial cache/result reuse requires matching solution, source inputs and assumptions. These fingerprints are not an immutable research archive.
- Updated individual and comprehensive Step 2/9 report paths delegate to shared conservative renderers. Duplicate legacy sections containing fabricated scores, inferred IRR or compliance claims were removed. Old scalar scores alone do not establish evaluation provenance. Financial CSV adds provenance.

## Validation

Use the repository lock without changing dependency pins:

```sh
uv sync --locked --python 3.11
uv run --locked python -m unittest discover -s tests -v
git diff --check
```

Local execution used CPython 3.11.16 with the unchanged lock: 35 tests discovered, 31 passed and 4 PostgreSQL integration tests explicitly skipped because no local test PostgreSQL server was available. Tests include actual Step 6 output fed into the optimizer, unchanged winners despite stale stored yields, energy accounting, date validation, cash-flow degradation/costs, report boundaries and Streamlit AppTest save/failure/cache behavior. Streamlit tests stub external services and database access.

The workflow `.github/workflows/research-repairs.yml` provisions disposable PostgreSQL 16 and runs the same suite with `BIPV_TEST_DATABASE_URL`. PostgreSQL tests create/drop only a uniquely named schema on the explicit loopback test database. They cover nullable/zero/percent metrics, legacy JSON, transaction rollback, project isolation of reads and weighted-rank metadata. The fixture represents the persistence interface under test; it is not verification of every live-schema variant. Do not call this CI passing until a completed run establishes it.

## Remaining gates

1. Full Replit/Streamlit workflow, project creation/loading, navigation and exports against a disposable copy of the actual deployment schema. The repository's base schema and application have pre-existing differences, including detailed-finance tables and optimization columns; compare them before rollout. Production IRR column precision may reject very large rates and needs review.
2. Time-resolved demand/generation balance and independent physics benchmarks (POA, shading, temperature, efficiency conventions and DC/AC losses). The shared yield is still `active area * annual irradiation * efficiency` before validated losses.
3. Validated forecasting, temporal holdout/baselines, growth assumptions, occupancy modifiers and uncertainty. No fitted ML model or measured forecast accuracy is introduced.
4. Authorization/ownership filtering for every project read/write before shared deployment.
5. Immutable run IDs, input snapshots and run-linked tables/reports before replacing thesis results. Successful saves still replace current project results. Preserve a verified archive before rerunning research projects.
6. Audit remaining legacy report/UI paths, old database claims and tariff/CO2 sources. Report consolidation here covers the reviewed Step 2 and Step 9 functions, not every historical artifact or other step.

Keep PR #1 draft pending these release gates. To undo the code, revert this follow-up commit; do not rewrite history. Reverting code cannot restore overwritten database rows and older code cannot interpret the new financial detail envelope. No such production rows were written by this task.
