from datetime import date

from src.assessment import (
    compare_landscapes, decommission_impact, orphaned_applications,
    run_data_quality_checks,
)
from src.factsheets import FactSheet, FactSheetType, Landscape, LifecycleEntry, LifecycleStage, Relationship
from src.sample_data import build_current_landscape, build_target_landscape


class TestCompareLandscapes:
    def test_finds_retirement_candidate_present_only_in_current(self):
        current = build_current_landscape()
        target = build_target_landscape()
        findings = compare_landscapes(current, target, as_of=date(2026, 6, 1))
        retiring = [f for f in findings if f.finding_type == "retiring_only_in_current"]
        assert any(f.factsheet_id == "app-legacy-scheduler" for f in retiring)

    def test_finds_new_planned_addition_present_only_in_target(self):
        current = build_current_landscape()
        target = build_target_landscape()
        findings = compare_landscapes(current, target, as_of=date(2026, 6, 1))
        new = [f for f in findings if f.finding_type == "new_in_target"]
        assert any(f.factsheet_id == "app-ai-quality-insights" for f in new)

    def test_finds_lifecycle_mismatch_for_shared_factsheet_on_different_components(self):
        current = build_current_landscape()
        target = build_target_landscape()
        findings = compare_landscapes(current, target, as_of=date(2026, 6, 1))
        # app-mes-core exists in both landscapes with the same lifecycle stage
        # (Active), so it should NOT be reported as a lifecycle mismatch even
        # though its runsOn relationship target changed.
        mismatches = [f for f in findings if f.finding_type == "lifecycle_mismatch"]
        assert not any(f.factsheet_id == "app-mes-core" for f in mismatches)

    def test_identical_landscapes_produce_no_findings(self):
        ls = build_current_landscape()
        findings = compare_landscapes(ls, ls, as_of=date(2026, 6, 1))
        assert findings == []

    def test_genuine_lifecycle_mismatch_is_detected(self):
        current = Landscape()
        target = Landscape()
        current.add_factsheet(FactSheet(
            id="x", name="X", type=FactSheetType.APPLICATION,
            lifecycle=[LifecycleEntry(LifecycleStage.ACTIVE, date(2020, 1, 1))],
        ))
        target.add_factsheet(FactSheet(
            id="x", name="X", type=FactSheetType.APPLICATION,
            lifecycle=[
                LifecycleEntry(LifecycleStage.ACTIVE, date(2020, 1, 1)),
                LifecycleEntry(LifecycleStage.PHASE_OUT, date(2025, 1, 1)),
            ],
        ))
        findings = compare_landscapes(current, target, as_of=date(2026, 1, 1))
        assert len(findings) == 1
        assert findings[0].finding_type == "lifecycle_mismatch"
        assert "PhaseOut" in findings[0].detail or "Active" in findings[0].detail


class TestDataQualityChecks:
    def test_missing_owner_is_flagged(self):
        ls = build_current_landscape()
        issues = run_data_quality_checks(ls)
        assert any(i.factsheet_id == "app-orphan-tool" and "owner" in i.issue.lower() for i in issues)

    def test_clean_factsheet_produces_no_issues(self):
        ls = Landscape()
        ls.add_factsheet(FactSheet(
            id="clean", name="Clean App", type=FactSheetType.APPLICATION,
            owner="Someone",
            lifecycle=[LifecycleEntry(LifecycleStage.ACTIVE, date(2020, 1, 1))],
        ))
        issues = run_data_quality_checks(ls)
        assert issues == []

    def test_no_lifecycle_entries_is_flagged(self):
        ls = Landscape()
        ls.add_factsheet(FactSheet(id="a", name="A", type=FactSheetType.APPLICATION, owner="Someone"))
        issues = run_data_quality_checks(ls)
        assert any("lifecycle" in i.issue.lower() for i in issues)

    def test_backward_lifecycle_transition_is_flagged(self):
        ls = Landscape()
        ls.add_factsheet(FactSheet(
            id="a", name="A", type=FactSheetType.APPLICATION, owner="Someone",
            lifecycle=[
                LifecycleEntry(LifecycleStage.ACTIVE, date(2020, 1, 1)),
                LifecycleEntry(LifecycleStage.PLAN, date(2021, 1, 1)),
            ],
        ))
        issues = run_data_quality_checks(ls)
        assert any("backward" in i.issue.lower() for i in issues)


class TestOrphanedApplications:
    def test_finds_application_with_no_runs_on_relationship(self):
        ls = build_current_landscape()
        orphans = orphaned_applications(ls)
        assert any(fs.id == "app-orphan-tool" for fs in orphans)

    def test_does_not_flag_application_with_runs_on_relationship(self):
        ls = build_current_landscape()
        orphans = orphaned_applications(ls)
        assert not any(fs.id == "app-mes-core" for fs in orphans)


class TestDecommissionImpact:
    def test_returns_direct_dependents_of_a_component(self):
        ls = build_current_landscape()
        impacted = decommission_impact(ls, "itc-onprem-db")
        assert set(impacted) == {"app-mes-core", "app-legacy-scheduler"}

    def test_returns_empty_list_for_factsheet_nothing_depends_on(self):
        ls = build_current_landscape()
        impacted = decommission_impact(ls, "app-quality-dashboard")
        assert impacted == []
