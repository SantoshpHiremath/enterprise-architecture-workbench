from datetime import date

import pytest

from src.factsheets import (
    FactSheet, FactSheetType, Landscape, LifecycleEntry, LifecycleStage,
    Relationship,
)


class TestLifecycleCurrentStage:
    def test_returns_none_before_any_lifecycle_entry(self):
        fs = FactSheet(
            id="a", name="A", type=FactSheetType.APPLICATION,
            lifecycle=[LifecycleEntry(LifecycleStage.ACTIVE, date(2024, 1, 1))],
        )
        assert fs.current_stage(date(2023, 1, 1)) is None

    def test_returns_active_stage_on_exact_start_date(self):
        fs = FactSheet(
            id="a", name="A", type=FactSheetType.APPLICATION,
            lifecycle=[LifecycleEntry(LifecycleStage.ACTIVE, date(2024, 1, 1))],
        )
        assert fs.current_stage(date(2024, 1, 1)) == LifecycleStage.ACTIVE

    def test_returns_most_recent_applicable_stage(self):
        fs = FactSheet(
            id="a", name="A", type=FactSheetType.APPLICATION,
            lifecycle=[
                LifecycleEntry(LifecycleStage.ACTIVE, date(2020, 1, 1)),
                LifecycleEntry(LifecycleStage.PHASE_OUT, date(2025, 1, 1)),
            ],
        )
        assert fs.current_stage(date(2022, 6, 1)) == LifecycleStage.ACTIVE
        assert fs.current_stage(date(2026, 1, 1)) == LifecycleStage.PHASE_OUT

    def test_is_active_true_only_during_active_stage(self):
        fs = FactSheet(
            id="a", name="A", type=FactSheetType.APPLICATION,
            lifecycle=[
                LifecycleEntry(LifecycleStage.ACTIVE, date(2020, 1, 1)),
                LifecycleEntry(LifecycleStage.END_OF_LIFE, date(2025, 1, 1)),
            ],
        )
        assert fs.is_active(date(2022, 1, 1)) is True
        assert fs.is_active(date(2026, 1, 1)) is False


class TestLifecycleValidation:
    def test_chronological_lifecycle_passes(self):
        fs = FactSheet(
            id="a", name="A", type=FactSheetType.APPLICATION,
            lifecycle=[
                LifecycleEntry(LifecycleStage.PLAN, date(2020, 1, 1)),
                LifecycleEntry(LifecycleStage.ACTIVE, date(2021, 1, 1)),
            ],
        )
        assert fs.lifecycle_is_chronological() is True

    def test_out_of_order_dates_fail(self):
        fs = FactSheet(
            id="a", name="A", type=FactSheetType.APPLICATION,
            lifecycle=[
                LifecycleEntry(LifecycleStage.ACTIVE, date(2021, 1, 1)),
                LifecycleEntry(LifecycleStage.PLAN, date(2020, 1, 1)),
            ],
        )
        assert fs.lifecycle_is_chronological() is False

    def test_duplicate_dates_fail(self):
        fs = FactSheet(
            id="a", name="A", type=FactSheetType.APPLICATION,
            lifecycle=[
                LifecycleEntry(LifecycleStage.PLAN, date(2020, 1, 1)),
                LifecycleEntry(LifecycleStage.ACTIVE, date(2020, 1, 1)),
            ],
        )
        assert fs.lifecycle_is_chronological() is False

    def test_valid_forward_stage_progression_passes(self):
        fs = FactSheet(
            id="a", name="A", type=FactSheetType.APPLICATION,
            lifecycle=[
                LifecycleEntry(LifecycleStage.PLAN, date(2020, 1, 1)),
                LifecycleEntry(LifecycleStage.PHASE_IN, date(2020, 6, 1)),
                LifecycleEntry(LifecycleStage.ACTIVE, date(2021, 1, 1)),
            ],
        )
        assert fs.lifecycle_follows_valid_stage_order() is True

    def test_backward_stage_transition_fails(self):
        fs = FactSheet(
            id="a", name="A", type=FactSheetType.APPLICATION,
            lifecycle=[
                LifecycleEntry(LifecycleStage.ACTIVE, date(2020, 1, 1)),
                LifecycleEntry(LifecycleStage.PLAN, date(2021, 1, 1)),
            ],
        )
        assert fs.lifecycle_follows_valid_stage_order() is False

    def test_repeated_same_stage_is_not_backward(self):
        fs = FactSheet(
            id="a", name="A", type=FactSheetType.APPLICATION,
            lifecycle=[
                LifecycleEntry(LifecycleStage.ACTIVE, date(2020, 1, 1)),
                LifecycleEntry(LifecycleStage.ACTIVE, date(2021, 1, 1)),
            ],
        )
        assert fs.lifecycle_follows_valid_stage_order() is True


class TestLandscapeFactSheets:
    def test_add_and_get_factsheet(self):
        ls = Landscape()
        fs = FactSheet(id="a", name="A", type=FactSheetType.APPLICATION)
        ls.add_factsheet(fs)
        assert ls.get("a") is fs

    def test_duplicate_id_rejected(self):
        ls = Landscape()
        ls.add_factsheet(FactSheet(id="a", name="A", type=FactSheetType.APPLICATION))
        with pytest.raises(ValueError):
            ls.add_factsheet(FactSheet(id="a", name="A2", type=FactSheetType.APPLICATION))

    def test_all_factsheets_filters_by_type(self):
        ls = Landscape()
        ls.add_factsheet(FactSheet(id="a", name="App", type=FactSheetType.APPLICATION))
        ls.add_factsheet(FactSheet(id="b", name="Comp", type=FactSheetType.IT_COMPONENT))
        apps = ls.all_factsheets(FactSheetType.APPLICATION)
        assert [fs.id for fs in apps] == ["a"]


class TestLandscapeRelationships:
    def _landscape_with_two_apps_one_component(self) -> Landscape:
        ls = Landscape()
        ls.add_factsheet(FactSheet(id="app1", name="App1", type=FactSheetType.APPLICATION))
        ls.add_factsheet(FactSheet(id="app2", name="App2", type=FactSheetType.APPLICATION))
        ls.add_factsheet(FactSheet(id="comp1", name="Comp1", type=FactSheetType.IT_COMPONENT))
        return ls

    def test_relationship_to_unknown_factsheet_rejected(self):
        ls = self._landscape_with_two_apps_one_component()
        with pytest.raises(ValueError):
            ls.add_relationship(Relationship("app1", "does-not-exist", "runsOn"))

    def test_relationships_from_and_to(self):
        ls = self._landscape_with_two_apps_one_component()
        ls.add_relationship(Relationship("app1", "comp1", "runsOn"))
        ls.add_relationship(Relationship("app2", "comp1", "runsOn"))
        assert len(ls.relationships_to("comp1")) == 2
        assert len(ls.relationships_from("app1")) == 1

    def test_dependents_of_returns_direct_dependents_only(self):
        ls = self._landscape_with_two_apps_one_component()
        ls.add_relationship(Relationship("app1", "comp1", "runsOn"))
        assert ls.dependents_of("comp1") == ["app1"]
        assert ls.dependents_of("app2") == []

    def test_transitive_dependencies_follows_chain(self):
        ls = Landscape()
        ls.add_factsheet(FactSheet(id="a", name="A", type=FactSheetType.APPLICATION))
        ls.add_factsheet(FactSheet(id="b", name="B", type=FactSheetType.APPLICATION))
        ls.add_factsheet(FactSheet(id="c", name="C", type=FactSheetType.IT_COMPONENT))
        ls.add_relationship(Relationship("a", "b", "dependsOn"))
        ls.add_relationship(Relationship("b", "c", "runsOn"))
        assert ls.transitive_dependencies("a") == {"b", "c"}

    def test_transitive_dependencies_handles_cycles_without_infinite_loop(self):
        ls = Landscape()
        ls.add_factsheet(FactSheet(id="a", name="A", type=FactSheetType.APPLICATION))
        ls.add_factsheet(FactSheet(id="b", name="B", type=FactSheetType.APPLICATION))
        ls.add_relationship(Relationship("a", "b", "dependsOn"))
        ls.add_relationship(Relationship("b", "a", "dependsOn"))
        # Must terminate and return a sane result rather than looping forever.
        assert ls.transitive_dependencies("a") == {"a", "b"}
