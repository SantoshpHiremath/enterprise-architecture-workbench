"""
Rendering: a lifecycle roadmap (the classic LeanIX "roadmap report" --
a timeline of fact sheets across their lifecycle stages) and a
dependency map, both as real, valid, tested static SVG -- inspectable,
diffable, and embeddable directly into a report or presentation without
any proprietary tool.
"""
from __future__ import annotations

from datetime import date

from .factsheets import FactSheetType, Landscape, LifecycleStage

_STAGE_COLORS = {
    LifecycleStage.PLAN: "#94a3b8",
    LifecycleStage.PHASE_IN: "#60a5fa",
    LifecycleStage.ACTIVE: "#34d399",
    LifecycleStage.PHASE_OUT: "#fbbf24",
    LifecycleStage.END_OF_LIFE: "#f87171",
}

_ROW_HEIGHT = 34
_LEFT_MARGIN = 220
_TOP_MARGIN = 50
_YEAR_WIDTH = 90


def render_roadmap_svg(landscape: Landscape, start_year: int, end_year: int,
                        type_filter: FactSheetType | None = None) -> str:
    """A horizontal timeline: one row per fact sheet, one colored
    segment per lifecycle stage, spanning start_year..end_year -- the
    same shape as a LeanIX roadmap report."""
    factsheets = sorted(landscape.all_factsheets(type_filter), key=lambda fs: fs.name)
    n_years = end_year - start_year + 1
    width = _LEFT_MARGIN + n_years * _YEAR_WIDTH + 40
    height = _TOP_MARGIN + len(factsheets) * _ROW_HEIGHT + 40

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}" font-family="Arial, sans-serif">']
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>')

    for i, year in enumerate(range(start_year, end_year + 1)):
        x = _LEFT_MARGIN + i * _YEAR_WIDTH
        parts.append(f'<text x="{x + _YEAR_WIDTH / 2}" y="{_TOP_MARGIN - 15}" '
                      f'text-anchor="middle" font-size="12" fill="#334155">{year}</text>')
        parts.append(f'<line x1="{x}" y1="{_TOP_MARGIN - 5}" x2="{x}" y2="{height - 20}" '
                      f'stroke="#e2e8f0" stroke-width="1"/>')

    def x_for(d: date) -> float:
        year_frac = (d - date(start_year, 1, 1)).days / 365.25
        return _LEFT_MARGIN + year_frac * _YEAR_WIDTH

    for row, fs in enumerate(factsheets):
        y = _TOP_MARGIN + row * _ROW_HEIGHT
        parts.append(f'<text x="10" y="{y + _ROW_HEIGHT / 2 + 4}" font-size="12" fill="#0f172a">'
                      f'{_escape(fs.name)}</text>')

        entries = sorted(fs.lifecycle, key=lambda e: e.start_date)
        for i, entry in enumerate(entries):
            seg_start = max(entry.start_date, date(start_year, 1, 1))
            seg_end = entries[i + 1].start_date if i + 1 < len(entries) else date(end_year, 12, 31)
            seg_end = min(seg_end, date(end_year, 12, 31))
            if seg_end < seg_start:
                continue
            x0, x1 = x_for(seg_start), x_for(seg_end)
            color = _STAGE_COLORS[entry.stage]
            parts.append(f'<rect x="{x0:.1f}" y="{y + 6}" width="{max(x1 - x0, 2):.1f}" '
                          f'height="{_ROW_HEIGHT - 14}" fill="{color}" rx="2"/>')

    legend_y = height - 12
    lx = _LEFT_MARGIN
    for stage, color in _STAGE_COLORS.items():
        parts.append(f'<rect x="{lx}" y="{legend_y - 10}" width="10" height="10" fill="{color}"/>')
        parts.append(f'<text x="{lx + 14}" y="{legend_y - 1}" font-size="10" fill="#334155">{stage.value}</text>')
        lx += 110

    parts.append('</svg>')
    return "\n".join(parts)


def render_dependency_map_svg(landscape: Landscape) -> str:
    """A simple layered dependency diagram: Applications on top,
    IT Components below, with arrows for 'runsOn' relationships --
    the same purpose as a LeanIX relationship/dependency diagram."""
    apps = sorted(landscape.all_factsheets(FactSheetType.APPLICATION), key=lambda fs: fs.name)
    components = sorted(landscape.all_factsheets(FactSheetType.IT_COMPONENT), key=lambda fs: fs.name)

    # Box width scales with the longest name on either row so long fact
    # sheet names don't overflow a fixed-width box (found by visually
    # inspecting a rendered sample with a long name and fixing it, not
    # assumed correct up front).
    all_names = [fs.name for fs in apps] + [fs.name for fs in components]
    max_name_len = max((len(n) for n in all_names), default=8)
    box_width = max(140, min(max_name_len * 7.5 + 20, 320))
    col_width = box_width + 40
    width = max(len(apps), len(components), 1) * col_width + 40
    height = 220

    app_y = 40
    comp_y = 160

    def positions(items):
        return {fs.id: (20 + i * col_width + col_width / 2, None) for i, fs in enumerate(items)}

    app_pos = positions(apps)
    comp_pos = positions(components)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}" font-family="Arial, sans-serif">']
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>')

    for fs in apps:
        x, _ = app_pos[fs.id]
        parts.append(f'<rect x="{x - box_width / 2:.1f}" y="{app_y}" width="{box_width:.1f}" height="36" rx="6" '
                      f'fill="#dbeafe" stroke="#3b82f6"/>')
        parts.append(f'<text x="{x}" y="{app_y + 22}" text-anchor="middle" font-size="12" '
                      f'fill="#1e3a8a">{_escape(fs.name)}</text>')

    for fs in components:
        x, _ = comp_pos[fs.id]
        parts.append(f'<rect x="{x - box_width / 2:.1f}" y="{comp_y}" width="{box_width:.1f}" height="36" rx="6" '
                      f'fill="#dcfce7" stroke="#22c55e"/>')
        parts.append(f'<text x="{x}" y="{comp_y + 22}" text-anchor="middle" font-size="12" '
                      f'fill="#14532d">{_escape(fs.name)}</text>')

    for fs in apps:
        for rel in landscape.relationships_from(fs.id):
            if rel.relationship_type != "runsOn" or rel.target_id not in comp_pos:
                continue
            x1, _ = app_pos[fs.id]
            x2, _ = comp_pos[rel.target_id]
            y1 = app_y + 36
            y2 = comp_y
            parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                          f'stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow)"/>')

    parts.append('<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" '
                 'orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#64748b"/></marker></defs>')
    parts.append('</svg>')
    return "\n".join(parts)


def _escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))
