import xml.etree.ElementTree as ET

from src.factsheets import FactSheetType
from src.sample_data import build_current_landscape
from src.visualize import render_dependency_map_svg, render_roadmap_svg


class TestRoadmapSvg:
    def test_produces_well_formed_xml(self):
        ls = build_current_landscape()
        svg = render_roadmap_svg(ls, 2018, 2027)
        # Will raise if not well-formed XML.
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg")

    def test_includes_a_row_label_for_every_factsheet(self):
        ls = build_current_landscape()
        svg = render_roadmap_svg(ls, 2018, 2027)
        for fs in ls.all_factsheets():
            assert fs.name in svg

    def test_type_filter_excludes_other_types(self):
        ls = build_current_landscape()
        svg = render_roadmap_svg(ls, 2018, 2027, type_filter=FactSheetType.IT_COMPONENT)
        assert "Shopfloor MES Core" not in svg
        assert "On-Prem SQL Cluster" in svg

    def test_special_characters_in_name_are_escaped(self):
        from datetime import date
        from src.factsheets import FactSheet, Landscape, LifecycleEntry, LifecycleStage

        ls = Landscape()
        ls.add_factsheet(FactSheet(
            id="a", name="R&D <Tool>", type=FactSheetType.APPLICATION,
            lifecycle=[LifecycleEntry(LifecycleStage.ACTIVE, date(2020, 1, 1))],
        ))
        svg = render_roadmap_svg(ls, 2018, 2027)
        assert "R&amp;D &lt;Tool&gt;" in svg
        # Must still be well-formed despite the special characters.
        ET.fromstring(svg)


class TestDependencyMapSvg:
    def test_produces_well_formed_xml(self):
        ls = build_current_landscape()
        svg = render_dependency_map_svg(ls)
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg")

    def test_includes_application_and_component_names(self):
        ls = build_current_landscape()
        svg = render_dependency_map_svg(ls)
        assert "Shopfloor MES Core" in svg
        assert "On-Prem SQL Cluster" in svg

    def test_empty_landscape_still_renders_valid_svg(self):
        from src.factsheets import Landscape
        svg = render_dependency_map_svg(Landscape())
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg")
