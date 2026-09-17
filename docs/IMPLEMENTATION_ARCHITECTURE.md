# BIPV Optimizer — implementation architecture

Status checked: 17 September 2026. This diagram describes the implemented PR #1 research workflow and the subsequently reported Replit candidate, **not a verified production deployment**. Repository baseline: `d3b5eb5a92940d8aa6447c12ad6ba553ca973f35`. Later Replit repairs require synchronization and release verification.

```mermaid
flowchart TB
  U["User"] --> A["Auth0 sign-in"]
  A --> P["Streamlit project workspace"]
  P --> I["BIM / facade inputs, weather, demand, PV specifications and tariffs"]
  I --> E["Annual radiation and gross PV generation scenario"]
  E --> W["Weighted genetic search"]
  E --> N["NSGA-II search"]
  W --> C["Compare methods and select solution"]
  N --> C
  C --> F["Annual-netting financial assessment"]
  I --> V["Separate research studies: interval balance, PV model and forecast evaluation"]
  F --> R["Reports and evidence export"]
  V --> R
  P --> G["Verified identity and project ownership checks"]
  G --> D[("PostgreSQL with row-level security")]
  F --> H["Immutable runs: inputs, results, provenance and parent links"]
  V --> H
  C --> H
  H --> G
  R --> G
```

## Reading the diagram

- The workspace's project reads and writes, including research runs and report retrieval, are subject to ownership checks and database row-level security. The identity boundary applies throughout; it is not a final reporting step. PostgreSQL stores project inputs/current results and immutable run evidence; transient Streamlit session state is not the durable record.
- Annual optimization uses active area, irradiation and fractional efficiency. It compares weighted genetic search and NSGA-II using common scenario inputs and constraints. Evaluation counts and run time are reported; equal population/generation settings do not imply equal evaluation budgets.
- The selected method and solution feed the financial calculation. Annual netting is not measured or time-matched self-consumption. Do not infer that annual gross generation is a fully loss-adjusted AC prediction.
- Separate research studies cover timestamp-matched energy balances and finance, a pvlib-based PV model with optional measured comparison, and chronological forecast evaluation against a seasonal-naive baseline. They do not silently replace annual candidate rankings.
- Saved evidence retains inputs, results, model version, hashes and parent optimization links. Historical records require explicit verified ownership assignment; no user automatically claims legacy projects.

## Boundaries and items requiring direct verification

- Numerical regression tests do not establish empirical facade accuracy. Shading/thermal calibration, measured validation, multiple optimizer seeds and sensitivity analysis remain research work.
- Do not label the financial horizon as fixed at 25 years without checking the active configuration.
- Do not describe all selectable elements as windows only without inspecting the active selection path.
- Carbon accounting and optional AI consultation, including Perplexity, require verification of the actual active implementation and dependencies. They are intentionally omitted from the verified core diagram.
- External weather/tariff sources require recorded provenance. An available adapter or API key is not proof that live requests succeed or that fallback data are suitable for research.
- Auth0 Free-plan billing was inspected separately; a successful dashboard administrator login does not validate application login/logout or two-account isolation.

## Release evidence and pending checks

GitHub baseline CI reported 57 passing tests. Replit subsequently reported successful restoration and migration rehearsals against database copies, preservation of project 126, runtime-lock alignment, and additional authentication/legacy-write repairs. These reports must be tied to the synchronized candidate revision before publishing. Production role verification, real-account access checks and explicit historical ownership decisions were still outstanding in the last completed release report. No production readiness or deployment is claimed by this document.

Sources: [PR #1](https://github.com/mgabr2007/BIPVoptimizer/pull/1), [research workflow and setup](MULTIUSER_RESEARCH_SETUP.md), and Replit inspection reports in the associated work session. Update this document after candidate synchronization and verified deployment.
