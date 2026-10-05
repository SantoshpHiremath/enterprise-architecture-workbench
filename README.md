# enterprise-architecture-workbench

A tested Python project modeling the core logic of enterprise architecture
management tooling such as LeanIX: fact sheets, lifecycles, dependencies,
current-vs-target architecture comparison, data quality checks, and
rendered roadmap/dependency visualizations. It supports documenting and
visualizing current and target architectures, creating reports, and
running architecture assessments and analyses.

## What it does

- **`src/factsheets.py`** — the `FactSheet` / `Landscape` / `Relationship`
  data model: typed fact sheets (Application, IT Component, Business
  Capability, Process) with a lifecycle history (Plan → Phase In → Active →
  Phase Out → End of Life), a directed relationship graph between them, and
  query methods (`current_stage`, `dependents_of`,
  `transitive_dependencies`) that answer the questions an architecture tool
  answers when you open a fact sheet. `transitive_dependencies` does a
  breadth-first graph walk and is tested against a genuine cycle to confirm
  it terminates.
- **`src/assessment.py`** — `compare_landscapes` does the current-vs-target
  diff: what's present only in current (retirement candidate), only in
  target (planned but not yet built), or present in both with a
  disagreeing lifecycle stage (a transition that's stalled). It also
  implements the data-quality checks (missing owner, missing or malformed
  lifecycle, backward stage transitions), orphaned-application detection,
  and decommission-impact lookup.
- **`src/visualize.py`** — renders two valid SVG reports: a lifecycle
  roadmap (one row per fact sheet, colored segments per lifecycle stage
  across a year range) and a layered dependency diagram (applications on
  top, IT components below, arrows for `runsOn` relationships). Both are
  tested for well-formed XML output and for correct handling of special
  characters in fact sheet names (`&`, `<`, `>` are escaped, verified by a
  dedicated test).
- **`run_pipeline.py`** — runs the full flow end to end against the sample
  landscape and writes three SVG files to `output/`.

## Scope

The project is a standalone implementation of the underlying data model
and the questions an architecture-assessment workflow needs answered; it
does not connect to a LeanIX tenant. All company, system, and application
names are fictional. The sample landscape (`src/sample_data.py`) is a small,
hand-built manufacturing-IT-style set of applications (a shop-floor MES, a
legacy scheduler being retired, a quality dashboard, a data warehouse
migration).

## Results

`python3 run_pipeline.py` runs against the sample landscape and produces
non-trivial findings: three retirement candidates, one planned addition,
one data-quality issue, a concrete two-application decommission-impact
answer, and three SVG files.

I also verified both rendered SVGs by screenshotting them in a headless
browser. That caught a layout issue the tests did not: the first dependency
map used a fixed 140px box width, and a longer name ("Undocumented
Reporting Macro Tool") overflowed its box. I fixed it by sizing the box
width to the longest name on the diagram and re-rendered to confirm.

## Tests

`python3 -m pytest` runs 38 tests, all passing, covering lifecycle stage
resolution and validation (including out-of-order dates and backward stage
transitions), the relationship graph (including a cycle-termination test),
the current-vs-target comparison logic (including a case confirming a
shared fact sheet with the *same* lifecycle stage in both landscapes does
NOT get falsely flagged), data quality checks, orphaned-application
detection, decommission-impact lookup, and SVG well-formedness/escaping.

## Running it

```bash
python3 -m pytest -v
python3 run_pipeline.py
# outputs: output/current_state_roadmap.svg, output/target_state_roadmap.svg,
#          output/current_dependency_map.svg
```

## Possible extensions

- Import and export fact sheets through the LeanIX API.
- Add further report types beyond the lifecycle roadmap and dependency map.
