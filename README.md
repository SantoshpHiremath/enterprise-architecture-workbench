# enterprise-architecture-workbench

A real, tested Python project modeling the core logic of enterprise
architecture management tooling (LeanIX being the specific product
named) — fact sheets, lifecycles, dependencies, current-vs-target
architecture comparison, data quality checks, and rendered roadmap/
dependency visualizations — built to close a specific gap identified
against Siemens AG's "Werkstudent Manufacturing IT" posting (Job ID
515604): "documenting and visualizing current and target architectures
in LeanIX, creating reports, and helping with architecture assessments
and analyses."

## What this is (read before citing anywhere)

**This is not LeanIX.** LeanIX is a licensed SaaS product — there is no
LeanIX tenant or API key available in this environment, and this
project does not connect to LeanIX in any way. What's built here is the
underlying data model and the questions an architecture-assessment
workflow actually needs answered, implemented as real, independently
verifiable Python: a fact sheet type system (Application, IT Component,
Business Capability, Process) with lifecycle stages (Plan → Phase In →
Active → Phase Out → End of Life), a relationship graph between fact
sheets, current-vs-target landscape comparison, data quality checks
matching LeanIX's own "quality seal" category of check (missing owner,
missing or malformed lifecycle, backward stage transitions), orphaned-
application detection, and decommission-impact queries — plus real,
rendered SVG output for a lifecycle roadmap and a dependency map, the
same two report types LeanIX itself produces.

**All company, system, and application names are fictional.** The
sample landscape (`src/sample_data.py`) is a small, hand-built
manufacturing-IT-style portfolio (a shop-floor MES, a legacy scheduler
being retired, a quality dashboard, a data warehouse migration) —
modeled to look like the domain this posting is in, not real Siemens
systems or data, which I have no access to.

## What this models

- **`src/factsheets.py`** — the `FactSheet` / `Landscape` / `Relationship`
  data model: typed fact sheets with a lifecycle history, a directed
  relationship graph between them, and query methods (`current_stage`,
  `dependents_of`, `transitive_dependencies`) that answer the same
  questions LeanIX's own UI answers when you click into a fact sheet.
  `transitive_dependencies` does a real breadth-first graph walk and is
  tested against a genuine cycle to confirm it terminates rather than
  looping forever — a real graph-algorithm correctness concern, not
  hypothetical.
- **`src/assessment.py`** — `compare_landscapes` does the actual current-
  vs-target diff: what's present only in current (retirement candidate),
  only in target (planned but not yet built), or present in both with a
  disagreeing lifecycle stage (a transition that's stalled). Also
  implements the data-quality checks, orphaned-application detection,
  and decommission-impact lookup.
- **`src/visualize.py`** — renders two real, valid SVG reports: a
  lifecycle roadmap (one row per fact sheet, colored segments per
  lifecycle stage across a year range) and a layered dependency diagram
  (applications on top, IT components below, arrows for `runsOn`
  relationships). Both are tested for well-formed XML output and for
  correct handling of special characters in fact sheet names (`&`, `<`,
  `>` are escaped, verified by a dedicated test).
- **`run_pipeline.py`** — runs the full flow end to end against the
  sample landscape and writes three real SVG files to `output/`.

## A bug found and fixed during this build

The first render of the dependency map used a fixed 140px box width for
every fact sheet name. A visual check (screenshotting the actual
rendered SVG, not just checking that tests passed) showed a longer name
("Undocumented Reporting Macro Tool") overflowing its box. Fixed by
sizing the box width to the longest name on the diagram instead of a
fixed constant, then re-rendered and re-screenshotted to confirm the fix
actually worked. This is disclosed here because it's a real example of
why visual verification matters beyond "all tests green" — the tests
checked well-formed SVG and correct escaping, but nothing checked
whether text stayed inside its box, which only a rendered screenshot
catches.

## Verification performed

- `python3 -m pytest` — 38 tests, all passing, covering lifecycle stage
  resolution and validation (including out-of-order dates and backward
  stage transitions), the relationship graph (including a cycle-
  termination test), the current-vs-target comparison logic (including
  a case designed to confirm a shared fact sheet with the *same*
  lifecycle stage in both landscapes does NOT get falsely flagged), data
  quality checks, orphaned-application detection, decommission-impact
  lookup, and SVG well-formedness/escaping.
- `python3 run_pipeline.py` — a real end-to-end run against the sample
  landscape, producing genuine, non-trivial findings (three retirement
  candidates, one planned addition, one real data-quality issue, a
  concrete two-application decommission-impact answer) and three real
  SVG files.
- Visual verification: both rendered SVGs were screenshotted via a
  headless browser and inspected directly — not just checked for valid
  XML — which is what caught the box-overflow bug above.

## Running it yourself

```bash
python3 -m pytest -v
python3 run_pipeline.py
# outputs: output/current_state_roadmap.svg, output/target_state_roadmap.svg,
#          output/current_dependency_map.svg
```
