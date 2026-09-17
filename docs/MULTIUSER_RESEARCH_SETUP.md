# Multi-user research workspace

PR #1 now supports individual OpenID Connect accounts, owned projects, immutable run evidence, weighted genetic search and NSGA-II comparison. The application is a research tool with explicit modelling assumptions, not a certified energy or financial assessment.

## Deployment setup

Use Python 3.11 and PostgreSQL 16. Install the tested lock:

```sh
uv sync --locked --python 3.11
```

Configure a dedicated PostgreSQL **migration/admin role** and a separate **application login role** without SUPERUSER, BYPASSRLS, schema ownership or membership in a privileged role. Keep both connection strings in your secret manager. The application role must not have CREATE permission on the application schema or permission to replace its functions. It is trusted server-side infrastructure; never expose SQL execution or its credentials to end users.

Back up the existing database and rehearse the migration against a disposable copy first. The migration is additive, widens financial numeric fields, creates ownership and history tables, and enables FORCE row-level security. It temporarily recreates the repository report view inside the migration transaction. Unknown dependent custom views require an explicit migration adaptation; they are never cascade-dropped. Old project rows remain unassigned and invisible to all application accounts.

Set `BIPV_MIGRATION_DATABASE_URL` to the admin connection, then run:

```sh
uv run python scripts/migrate.py --runtime-role bipv_app
```

Set `DATABASE_URL` to the nonprivileged application connection. For legacy Step 4/5 adapters, also provide matching `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, and `PGPASSWORD`. Use provider-required TLS settings in the connection configuration. Never run the web process with migration credentials.

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and enter the OIDC client configuration. Register the exact `/oauth2callback` redirect URI in the identity provider. Use a long random cookie secret and HTTPS for deployment. Restrict who can register/sign in through the identity provider. The application identifies accounts by the pair of verified `iss` and `sub` claims, not email address, query parameters or a client-supplied project ID. It does not maintain passwords. Missing authentication configuration leaves the application on its sign-in screen.

```sh
uv run streamlit run app.py
```

Before opening the service to users, verify real OIDC login/logout, expired-session handling, two distinct accounts, same-named projects under different owners, and denied cross-account access. AppTest verifies the application gate with test claims, not a live identity-provider handshake.

For each historical project that should become accessible, obtain the correct account's issuer/subject from the identity provider and map its explicit project ID with admin credentials:

```sh
uv run python scripts/assign_project_owner.py --project-id 123 --issuer https://your-provider.example --subject your-verified-subject
```

This command only assigns an unowned project; it cannot silently transfer an already-owned project. Administrative account suspension uses `app_users.disabled`; new connections fail closed for suspended users. Do not grant application users permission to edit this field. FORCE RLS and nonprivileged connection checks cover the shared database manager and raw legacy connection paths. An application connection is bound to one verified identity; async connections rebind on acquisition.

## Research workflow

1. Sign in, create/select your project, and complete the existing input stages. Regenerate ambiguous old Step 6/8 records; percentage/fraction and missing energy metadata are rejected.
2. In Step 8 choose weighted search, NSGA-II, or Compare both. Comparison uses the same inputs, seed, population, generations, tariffs and coverage constraint. Evaluation counts and run time are reported because the methods use different evaluation budgets. Weighted preferences rank candidates; NSGA-II survival uses nondominated sorting and crowding. Its three objectives are minimum capital cost, maximum annual generation and maximum first-year net ROI. Choose which method's results to carry forward.
3. In Step 9 choose a particular solution for finance. Cash flows include separate import/export tariffs, degradation, O&M, replacement, upfront incentives and escalation. IRR is nullable, with explicit percent units. Unavailable results are not replaced with zeros. Upstream fingerprints prevent use of stale results.
4. Use Research Validation for time-matched studies, a PV model/measured comparison, or evaluated forecasting. Enter dataset provenance and upload observations in the documented column/interval formats. Each save retains the entire input and output under the current project's ownership.
5. Run History lists immutable evidence, model versions, input hashes and parent optimization runs. Download the complete JSON evidence. Rerunning optimization or finance replaces current display rows while retaining prior saved runs. Before the first replacement, surviving unversioned results are archived as `legacy-unverified`; already-deleted past data cannot be reconstructed. Projects with research runs cannot be deleted through cascading SQL. There is no automatic ownership transfer or history purge.

## What each calculation establishes

| Path | Implemented evidence | Scope and remaining requirements |
|---|---|---|
| Step 8/9 annual workflow | Consistent active area × irradiation × fractional efficiency and separately priced annual netting | Experimental gross annual generation, before explicit AC losses. Annual netting is not time-matched self-consumption. |
| Time-matched research study | Interval-by-interval generation = self-use + export; demand = self-use + import; complete UTC year and leap-year checks | No storage/curtailment. Profiles must represent the stated investment. This study does not rerank annual optimizer candidates. |
| Time-matched finance | Same cash-flow engine; degradation applied to every interval before rebalancing; costs/incentives/replacement retained | Constant repeated demand pattern; common import/export price escalation scenario. Future tariffs and demand remain assumptions. |
| PV model | pvlib isotropic POA, selected SAPM mounting temperature, linear temperature-adjusted DC, fixed inverter efficiency and clipping | Numerical checks cover diffuse-horizontal geometry, night zero output, clipping and interval integration. Geometry-based shading, spectral/mismatch/soiling models, facade thermal calibration and independent field validation remain research requirements. |
| Measured PV comparison | MAE, RMSE and bias against uploaded interval-aligned measured generation | Dataset quality, sensor calibration and representative validation periods must be established by the researcher. No universal accuracy threshold is invented. |
| Forecast evaluation | Fixed-origin recursive last-12-month holdout, random forest versus seasonal-naive baseline, errors on observations; separately refitted next-12-month forecast | At least 36 consecutive observed months. One holdout year, no calibrated prediction intervals or multi-decade accuracy claims. The legacy long-range path remains a scenario. |
| Optimizer comparison | Seeded weighted search and DEAP NSGA-II; exhaustive three-element oracle in regression coverage | The Pareto front is among evaluated feasible candidates, not proof of a global front. Research conclusions need multiple seeds, budget-matched studies and sensitivity analysis. |

## Verification and release gates

Run `uv run python -m unittest discover -s tests -v`. Database tests run only with an explicit loopback `BIPV_TEST_DATABASE_URL`; they create isolated random schemas and nonprivileged roles. GitHub Actions supplies disposable PostgreSQL 16. The tests cover ownership reads/writes, async rebinding, report-view isolation, immutable/linked runs, migration replay, financial rollback/round trips, input persistence and both searches, plus Streamlit startup and financial-save behavior.

Before production deployment: verify the actual database copy (including custom views, existing policies, duplicate element IDs and privilege grants), complete the live OIDC two-account check, configure backups/access logging/retention, and review the remaining source/provenance claims in legacy product catalogs and reports. Legacy Step 4/5 imports are repaired with a Pandera version compatible with the pinned pandas/NumPy stack and Pydantic v1 settings compatibility. The old enhanced radiation adapter produced orientation-based placeholder values and is explicitly disabled; use the new PV study with timestamped weather. Other annual radiation pathways remain experimental and require independent validation.

No production database migration, deployment or merge is performed by this PR. A successful CI run establishes the tested repository schema and numerical contracts, not production readiness or field accuracy.

References: [Streamlit authentication](https://docs.streamlit.io/develop/concepts/connections/authentication), [PostgreSQL row security](https://www.postgresql.org/docs/16/ddl-rowsecurity.html), [DEAP NSGA-II](https://deap.readthedocs.io/en/master/api/tools.html#deap.tools.selNSGA2), [pvlib transposition](https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.irradiance.get_total_irradiance.html), [SAPM temperature](https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.temperature.sapm_cell.html).
