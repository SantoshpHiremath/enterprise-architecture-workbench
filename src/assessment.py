"""
Architecture assessment logic: comparing a current-state landscape
against a target-state landscape, and surfacing the kind of findings a
Reference Architecture / Enterprise Architecture team actually reports
on -- what's retiring, what's new, what's stuck mid-transition, and
where lifecycle data itself looks wrong.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .factsheets import FactSheet, FactSheetType, Landscape, LifecycleStage


@dataclass
class GapFinding:
    factsheet_id: str
    factsheet_name: str
    finding_type: str  # "retiring_only_in_current", "new_in_target", "lifecycle_mismatch"
    detail: str


def compare_landscapes(current: Landscape, target: Landscape, as_of: date) -> list[GapFinding]:
    """The core current-vs-target comparison: what exists in current
    but not target (candidates for retirement), what exists in target
    but not current (planned additions not yet realized), and fact
    sheets present in both whose lifecycle stage disagrees between the
    two landscapes (e.g. current says Active, target says PhaseOut --
    a real signal the transition hasn't started yet)."""
    current_ids = {fs.id for fs in current.all_factsheets()}
    target_ids = {fs.id for fs in target.all_factsheets()}

    findings: list[GapFinding] = []

    for fs_id in sorted(current_ids - target_ids):
        fs = current.get(fs_id)
        findings.append(GapFinding(
            factsheet_id=fs_id,
            factsheet_name=fs.name,
            finding_type="retiring_only_in_current",
            detail=f"{fs.name} exists in the current architecture but is absent from the target -- a retirement candidate.",
        ))

    for fs_id in sorted(target_ids - current_ids):
        fs = target.get(fs_id)
        findings.append(GapFinding(
            factsheet_id=fs_id,
            factsheet_name=fs.name,
            finding_type="new_in_target",
            detail=f"{fs.name} is planned in the target architecture but does not exist yet in the current one.",
        ))

    for fs_id in sorted(current_ids & target_ids):
        cur_fs = current.get(fs_id)
        tgt_fs = target.get(fs_id)
        cur_stage = cur_fs.current_stage(as_of)
        tgt_stage = tgt_fs.current_stage(as_of)
        if cur_stage != tgt_stage:
            findings.append(GapFinding(
                factsheet_id=fs_id,
                factsheet_name=cur_fs.name,
                finding_type="lifecycle_mismatch",
                detail=(
                    f"{cur_fs.name}: current architecture has it at stage "
                    f"{cur_stage.value if cur_stage else 'unstarted'}, but the target "
                    f"architecture expects {tgt_stage.value if tgt_stage else 'unstarted'}."
                ),
            ))

    return findings


@dataclass
class DataQualityIssue:
    factsheet_id: str
    factsheet_name: str
    issue: str


def run_data_quality_checks(landscape: Landscape) -> list[DataQualityIssue]:
    """Fact-sheet-level data quality checks -- the same category of
    check LeanIX's own quality-seal feature runs: is required data
    present and internally consistent, not just 'does the record
    exist.'"""
    issues: list[DataQualityIssue] = []

    for fs in landscape.all_factsheets():
        if not fs.owner:
            issues.append(DataQualityIssue(fs.id, fs.name, "Missing owner"))

        if not fs.lifecycle:
            issues.append(DataQualityIssue(fs.id, fs.name, "No lifecycle entries defined"))
            continue

        if not fs.lifecycle_is_chronological():
            issues.append(DataQualityIssue(
                fs.id, fs.name,
                "Lifecycle entries are not in chronological order or contain duplicate dates",
            ))

        if not fs.lifecycle_follows_valid_stage_order():
            issues.append(DataQualityIssue(
                fs.id, fs.name,
                "Lifecycle stages move backward (e.g. Active -> Plan), which is not a valid transition",
            ))

    return issues


def orphaned_applications(landscape: Landscape) -> list[FactSheet]:
    """Applications with no IT Component relationship at all -- a real
    architecture smell: either the dependency was never documented, or
    the application genuinely runs on nothing tracked, both worth
    flagging for review."""
    orphans = []
    for fs in landscape.all_factsheets(FactSheetType.APPLICATION):
        outgoing = landscape.relationships_from(fs.id)
        if not any(r.relationship_type == "runsOn" for r in outgoing):
            orphans.append(fs)
    return orphans


def decommission_impact(landscape: Landscape, factsheet_id: str) -> list[str]:
    """The direct-dependents query an architect runs before proposing
    to retire something: who breaks if this goes away."""
    return landscape.dependents_of(factsheet_id)
