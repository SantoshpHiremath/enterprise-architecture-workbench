"""
End-to-end run: build a sample current and target manufacturing-IT-style
landscape, run the architecture assessment (gap comparison, data quality
checks, orphaned applications, decommission impact), and render both a
lifecycle roadmap and a dependency map to real SVG files in output/.

Run: python3 run_pipeline.py
"""
from datetime import date

from src.assessment import (
    compare_landscapes, decommission_impact, orphaned_applications,
    run_data_quality_checks,
)
from src.sample_data import build_current_landscape, build_target_landscape
from src.visualize import render_dependency_map_svg, render_roadmap_svg


def main() -> None:
    current = build_current_landscape()
    target = build_target_landscape()
    as_of = date(2026, 6, 1)

    print("=" * 70)
    print("ARCHITECTURE ASSESSMENT: current vs. target landscape")
    print("=" * 70)
    findings = compare_landscapes(current, target, as_of=as_of)
    if not findings:
        print("No gaps found -- current and target landscapes are aligned.")
    for f in findings:
        print(f"[{f.finding_type}] {f.detail}")

    print()
    print("=" * 70)
    print("DATA QUALITY CHECKS (current landscape)")
    print("=" * 70)
    issues = run_data_quality_checks(current)
    if not issues:
        print("No data quality issues found.")
    for issue in issues:
        print(f"[{issue.factsheet_name}] {issue.issue}")

    print()
    print("=" * 70)
    print("ORPHANED APPLICATIONS (no runsOn relationship)")
    print("=" * 70)
    orphans = orphaned_applications(current)
    if not orphans:
        print("No orphaned applications.")
    for fs in orphans:
        print(f"- {fs.name} ({fs.id})")

    print()
    print("=" * 70)
    print("DECOMMISSION IMPACT: what depends on 'On-Prem SQL Cluster'?")
    print("=" * 70)
    impacted = decommission_impact(current, "itc-onprem-db")
    for dep_id in impacted:
        print(f"- {current.get(dep_id).name}")
    print(
        f"\n-> Retiring the on-prem SQL cluster would directly impact "
        f"{len(impacted)} application(s). This is exactly the kind of "
        f"question a Reference Architecture team answers before proposing "
        f"a decommission."
    )

    print()
    print("=" * 70)
    print("RENDERING REPORTS")
    print("=" * 70)

    roadmap_svg = render_roadmap_svg(current, start_year=2018, end_year=2027)
    with open("output/current_state_roadmap.svg", "w") as f:
        f.write(roadmap_svg)
    print(f"Wrote output/current_state_roadmap.svg ({len(roadmap_svg)} bytes)")

    target_roadmap_svg = render_roadmap_svg(target, start_year=2018, end_year=2027)
    with open("output/target_state_roadmap.svg", "w") as f:
        f.write(target_roadmap_svg)
    print(f"Wrote output/target_state_roadmap.svg ({len(target_roadmap_svg)} bytes)")

    dep_map_svg = render_dependency_map_svg(current)
    with open("output/current_dependency_map.svg", "w") as f:
        f.write(dep_map_svg)
    print(f"Wrote output/current_dependency_map.svg ({len(dep_map_svg)} bytes)")


if __name__ == "__main__":
    main()
