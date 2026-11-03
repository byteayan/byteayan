"""Draw the stats and languages cards as SVG files committed to the repo."""

from collections import Counter
from html import escape
from pathlib import PurePosixPath

# Extension -> (language, colour). Colours follow GitHub's linguist palette.
LANGUAGES = {
    ".java": ("Java", "#b07219"),
    ".py": ("Python", "#3572A5"),
    ".ts": ("TypeScript", "#3178c6"),
    ".tsx": ("TypeScript", "#3178c6"),
    ".js": ("JavaScript", "#f1e05a"),
    ".cjs": ("JavaScript", "#f1e05a"),
    ".mjs": ("JavaScript", "#f1e05a"),
    ".svelte": ("Svelte", "#ff3e00"),
    ".vue": ("Vue", "#41b883"),
    ".scala": ("Scala", "#c22d40"),
    ".sh": ("Shell", "#89e051"),
    ".md": ("Markdown", "#083fa1"),
    ".rst": ("reStructuredText", "#b6c2d1"),
    ".yaml": ("YAML", "#cb171e"),
    ".yml": ("YAML", "#cb171e"),
    ".tpl": ("Helm", "#0f1689"),
    ".css": ("CSS", "#663399"),
    ".html": ("HTML", "#e34c26"),
    ".hbs": ("Handlebars", "#f7931e"),
}
OTHER_COLOUR = "#8b949e"
SKIPPED_FILES = {"pnpm-lock.yaml", "package-lock.json", "yarn.lock"}
# Data and config formats that GitHub's own language stats leave out too.
SKIPPED_SUFFIXES = {".json", ".xml", ".txt", ".csv", ".lock", ".svg", ".png", ".jpg"}

STYLE = """<style>
  .title { font: 600 18px 'Segoe UI', -apple-system, Ubuntu, sans-serif; fill: #38C2FF; }
  .label { font: 400 14px 'Segoe UI', -apple-system, Ubuntu, sans-serif; fill: #BDC3CF; }
  .value { font: 600 14px 'Segoe UI', -apple-system, Ubuntu, sans-serif; fill: #E6EDF3; }
</style>"""


def background(width, height):
    # A solid card keeps the text readable whichever theme GitHub is showing.
    return (f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="6" '
            'fill="#0d1117" stroke="#30363d"/>')


def language_of(filename):
    path = PurePosixPath(filename)
    suffix = path.suffix.lower()
    if path.name in SKIPPED_FILES or suffix in SKIPPED_SUFFIXES or ".changeset" in path.parts:
        return None
    if path.name.startswith("Dockerfile"):
        return ("Dockerfile", "#384d54")
    return LANGUAGES.get(suffix, ("Other", OTHER_COLOUR))


def language_totals(files):
    """Sum changed lines per language over (filename, changes) pairs."""
    totals, colours = Counter(), {}
    for filename, changes in files:
        lang = language_of(filename)
        if lang and changes:
            totals[lang[0]] += changes
            colours[lang[0]] = lang[1]
    return totals, colours


def stats_card(rows):
    """rows: list of (label, value) pairs."""
    height = 64 + 28 * len(rows)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="{height}" viewBox="0 0 400 {height}">',
        STYLE,
        background(400, height),
        '<text x="25" y="35" class="title">Upstream contributions</text>',
    ]
    for i, (label, value) in enumerate(rows):
        y = 70 + 28 * i
        lines.append(f'<text x="25" y="{y}" class="label">{escape(label)}</text>')
        lines.append(f'<text x="375" y="{y}" class="value" text-anchor="end">{value:,}</text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def languages_card(totals, colours, limit=6):
    # "Other" never takes a top slot; it collects unknown files plus the tail.
    top = [(name, n) for name, n in totals.most_common() if name != "Other"][:limit]
    rest = sum(totals.values()) - sum(n for _, n in top)
    if rest:
        top.append(("Other", rest))
        colours = {**colours, "Other": OTHER_COLOUR}
    grand = sum(n for _, n in top) or 1

    width, bar_w = 445, 395
    rows = (len(top) + 1) // 2
    height = 95 + 26 * rows
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        STYLE,
        background(width, height),
        '<text x="25" y="35" class="title">Languages in my PRs</text>',
        '<clipPath id="bar"><rect x="25" y="52" width="395" height="8" rx="4"/></clipPath>',
        '<g clip-path="url(#bar)">',
    ]
    x = 25.0
    for name, n in top:
        w = bar_w * n / grand
        lines.append(f'<rect x="{x:.2f}" y="52" width="{w:.2f}" height="8" fill="{colours[name]}"/>')
        x += w
    lines.append("</g>")
    for i, (name, n) in enumerate(top):
        col, row = i % 2, i // 2
        cx, cy = 30 + 200 * col, 88 + 26 * row
        pct = f"{100 * n / grand:.1f}%"
        lines.append(f'<circle cx="{cx}" cy="{cy - 5}" r="5" fill="{colours[name]}"/>')
        lines.append(f'<text x="{cx + 12}" y="{cy}" class="label">{escape(name)} <tspan class="value">{pct}</tspan></text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"
