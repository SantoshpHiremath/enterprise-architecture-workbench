"""
A small, hand-built sample landscape modeled loosely on a
manufacturing-IT-style application portfolio (MES, ERP integration,
shop-floor data collection, reporting) -- entirely fictional company
and system names, not real Siemens systems or data. Used to exercise
the assessment and visualization code with a landscape that actually
looks like the domain this posting is in.
"""
from __future__ import annotations

from datetime import date

from .factsheets import (
    FactSheet, FactSheetType, LifecycleEntry, LifecycleStage, Landscape,
    Relationship,
)


def build_current_landscape() -> Landscape:
    ls = Landscape()

    ls.add_factsheet(FactSheet(
        id="app-mes-core", name="Shopfloor MES Core", type=FactSheetType.APPLICATION,
        owner="Manufacturing IT",
        lifecycle=[LifecycleEntry(LifecycleStage.ACTIVE, date(2019, 1, 1))],
    ))
    ls.add_factsheet(FactSheet(
        id="app-legacy-scheduler", name="Legacy Production Scheduler", type=FactSheetType.APPLICATION,
        owner="Manufacturing IT",
        lifecycle=[
            LifecycleEntry(LifecycleStage.ACTIVE, date(2012, 1, 1)),
            LifecycleEntry(LifecycleStage.PHASE_OUT, date(2025, 1, 1)),
        ],
    ))
    ls.add_factsheet(FactSheet(
        id="app-quality-dashboard", name="Quality Reporting Dashboard", type=FactSheetType.APPLICATION,
        owner="Manufacturing IT",
        lifecycle=[LifecycleEntry(LifecycleStage.ACTIVE, date(2022, 6, 1))],
    ))
    ls.add_factsheet(FactSheet(
        id="app-orphan-tool", name="Undocumented Reporting Macro Tool", type=FactSheetType.APPLICATION,
        owner="",  # deliberately missing -- exercised by the data-quality check
        lifecycle=[LifecycleEntry(LifecycleStage.ACTIVE, date(2016, 1, 1))],
    ))

    ls.add_factsheet(FactSheet(
        id="itc-onprem-db", name="On-Prem SQL Cluster", type=FactSheetType.IT_COMPONENT,
        owner="Infrastructure",
        lifecycle=[LifecycleEntry(LifecycleStage.ACTIVE, date(2015, 1, 1))],
    ))
    ls.add_factsheet(FactSheet(
        id="itc-cloud-dw", name="Cloud Data Warehouse", type=FactSheetType.IT_COMPONENT,
        owner="Infrastructure",
        lifecycle=[LifecycleEntry(LifecycleStage.ACTIVE, date(2023, 1, 1))],
    ))

    ls.add_relationship(Relationship("app-mes-core", "itc-onprem-db", "runsOn"))
    ls.add_relationship(Relationship("app-legacy-scheduler", "itc-onprem-db", "runsOn"))
    ls.add_relationship(Relationship("app-quality-dashboard", "itc-cloud-dw", "runsOn"))
    ls.add_relationship(Relationship("app-quality-dashboard", "app-mes-core", "dependsOn"))
    # app-orphan-tool deliberately has no runsOn relationship at all.

    return ls


def build_target_landscape() -> Landscape:
    ls = Landscape()

    ls.add_factsheet(FactSheet(
        id="app-mes-core", name="Shopfloor MES Core", type=FactSheetType.APPLICATION,
        owner="Manufacturing IT",
        lifecycle=[LifecycleEntry(LifecycleStage.ACTIVE, date(2019, 1, 1))],
    ))
    # app-legacy-scheduler is absent from target -- planned retirement.
    ls.add_factsheet(FactSheet(
        id="app-quality-dashboard", name="Quality Reporting Dashboard", type=FactSheetType.APPLICATION,
        owner="Manufacturing IT",
        lifecycle=[LifecycleEntry(LifecycleStage.ACTIVE, date(2022, 6, 1))],
    ))
    ls.add_factsheet(FactSheet(
        id="app-ai-quality-insights", name="AI Quality Insights Service", type=FactSheetType.APPLICATION,
        owner="Manufacturing IT",
        lifecycle=[LifecycleEntry(LifecycleStage.PLAN, date(2026, 9, 1))],
    ))

    ls.add_factsheet(FactSheet(
        id="itc-cloud-dw", name="Cloud Data Warehouse", type=FactSheetType.IT_COMPONENT,
        owner="Infrastructure",
        lifecycle=[LifecycleEntry(LifecycleStage.ACTIVE, date(2023, 1, 1))],
    ))

    ls.add_relationship(Relationship("app-mes-core", "itc-cloud-dw", "runsOn"))
    ls.add_relationship(Relationship("app-quality-dashboard", "itc-cloud-dw", "runsOn"))
    ls.add_relationship(Relationship("app-ai-quality-insights", "itc-cloud-dw", "runsOn"))
    ls.add_relationship(Relationship("app-ai-quality-insights", "app-quality-dashboard", "dependsOn"))

    return ls
