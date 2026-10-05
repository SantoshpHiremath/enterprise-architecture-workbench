"""
Fact sheet data model — the core object LeanIX (and enterprise
architecture management tooling generally) is built around: a typed,
attributed record for an Application, IT Component, Business Capability,
or Process, each with a lifecycle and relationships to other fact sheets.

This is a standalone model and does not connect to a LeanIX tenant.
What's modeled here is the underlying
data structure and the questions an architecture-assessment workflow
actually needs answered: what exists, what stage of its lifecycle is it
in, what does it depend on, and does the current landscape match the
target one.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class FactSheetType(Enum):
    APPLICATION = "Application"
    IT_COMPONENT = "ITComponent"
    BUSINESS_CAPABILITY = "BusinessCapability"
    PROCESS = "Process"


class LifecycleStage(Enum):
    PLAN = "Plan"
    PHASE_IN = "PhaseIn"
    ACTIVE = "Active"
    PHASE_OUT = "PhaseOut"
    END_OF_LIFE = "EndOfLife"


# The order lifecycle stages progress through. Used to detect an
# impossible transition (e.g. EndOfLife -> Active) during validation.
_STAGE_ORDER = [
    LifecycleStage.PLAN,
    LifecycleStage.PHASE_IN,
    LifecycleStage.ACTIVE,
    LifecycleStage.PHASE_OUT,
    LifecycleStage.END_OF_LIFE,
]


@dataclass
class LifecycleEntry:
    stage: LifecycleStage
    start_date: date


@dataclass
class FactSheet:
    id: str
    name: str
    type: FactSheetType
    lifecycle: list[LifecycleEntry] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    owner: str = ""
    description: str = ""

    def current_stage(self, as_of: date) -> LifecycleStage | None:
        """The lifecycle stage active on a given date, or None if the
        fact sheet's lifecycle hadn't started yet as of that date."""
        applicable = [e for e in self.lifecycle if e.start_date <= as_of]
        if not applicable:
            return None
        return max(applicable, key=lambda e: e.start_date).stage

    def is_active(self, as_of: date) -> bool:
        return self.current_stage(as_of) == LifecycleStage.ACTIVE

    def lifecycle_is_chronological(self) -> bool:
        """True if lifecycle entries are sorted by ascending start_date
        with no duplicate dates -- a basic data-quality check LeanIX
        itself flags when a fact sheet's lifecycle is entered out of
        order."""
        dates = [e.start_date for e in self.lifecycle]
        return dates == sorted(dates) and len(dates) == len(set(dates))

    def lifecycle_follows_valid_stage_order(self) -> bool:
        """True if the sequence of stages (ignoring dates) never moves
        backward in the standard Plan -> PhaseIn -> Active -> PhaseOut
        -> EndOfLife progression. A fact sheet that goes straight from
        Active back to Plan, for example, is a real data-entry error
        this check is designed to catch."""
        indices = [_STAGE_ORDER.index(e.stage) for e in self.lifecycle]
        return all(b >= a for a, b in zip(indices, indices[1:]))


@dataclass
class Relationship:
    """A directed dependency between two fact sheets, e.g. an
    Application 'runs on' an IT Component, or a Process 'is supported
    by' an Application -- LeanIX's relationship model, simplified to
    the parts an architecture assessment actually queries."""
    source_id: str
    target_id: str
    relationship_type: str  # e.g. "runsOn", "supports", "dependsOn"


class Landscape:
    """A collection of fact sheets and their relationships -- the
    equivalent of a LeanIX workspace, scoped down to what's needed to
    run real architecture-assessment queries against it."""

    def __init__(self) -> None:
        self._factsheets: dict[str, FactSheet] = {}
        self._relationships: list[Relationship] = []

    def add_factsheet(self, fs: FactSheet) -> None:
        if fs.id in self._factsheets:
            raise ValueError(f"Fact sheet with id {fs.id!r} already exists")
        self._factsheets[fs.id] = fs

    def add_relationship(self, rel: Relationship) -> None:
        for endpoint in (rel.source_id, rel.target_id):
            if endpoint not in self._factsheets:
                raise ValueError(f"Unknown fact sheet id in relationship: {endpoint!r}")
        self._relationships.append(rel)

    def get(self, factsheet_id: str) -> FactSheet:
        return self._factsheets[factsheet_id]

    def all_factsheets(self, type_: FactSheetType | None = None) -> list[FactSheet]:
        fs = list(self._factsheets.values())
        if type_ is not None:
            fs = [f for f in fs if f.type == type_]
        return fs

    def relationships_from(self, factsheet_id: str) -> list[Relationship]:
        return [r for r in self._relationships if r.source_id == factsheet_id]

    def relationships_to(self, factsheet_id: str) -> list[Relationship]:
        return [r for r in self._relationships if r.target_id == factsheet_id]

    def dependents_of(self, factsheet_id: str) -> list[str]:
        """IDs of fact sheets that depend on the given one -- the
        question an architect asks before decommissioning something:
        'what breaks if I retire this?'"""
        return [r.source_id for r in self._relationships if r.target_id == factsheet_id]

    def transitive_dependencies(self, factsheet_id: str) -> set[str]:
        """All fact sheets (direct and indirect) that the given fact
        sheet depends on, via a breadth-first walk of the relationship
        graph. Guards against cycles."""
        seen: set[str] = set()
        frontier = [factsheet_id]
        while frontier:
            current = frontier.pop()
            for rel in self.relationships_from(current):
                if rel.target_id not in seen:
                    seen.add(rel.target_id)
                    frontier.append(rel.target_id)
        return seen
