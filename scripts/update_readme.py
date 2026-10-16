#!/usr/bin/env python3
"""Render README.md from README.template.md with live pull request data."""

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USER = "byteayan"
ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "README.template.md"
README = ROOT / "README.md"
HEADER = "<!-- AUTO-GENERATED from README.template.md — do not edit by hand -->\n"
UPDATED_RE = re.compile(r"Auto-updated [^·]*·")

PROJECTS = [
    {
        "name": "Apache HugeGraph",
        "repos": ["apache/hugegraph", "apache/hugegraph-doc"],
        "focus": "Server fixes, Docker and Helm config, crash diagnostics, dead-code removal, deployment docs.",
    },
    {
        "name": "Open Food Facts",
        "repos": ["openfoodfacts/openfoodfacts-explorer", "openfoodfacts/open-prices-frontend"],
        "focus": "Explorer (SvelteKit) and Open Prices (Vue) fixes: links, forms, the proof assistant, product comparison.",
    },
    {
        "name": "Zulip",
        "repos": ["zulip/zulip"],
        "focus": "Cache flushing when email visibility changes, status emoji rendering.",
    },
    {
        "name": "Rocket.Chat",
        "repos": ["RocketChat/Rocket.Chat"],
        "focus": "UI fixes for the home page and the emoji picker.",
    },
    {
        "name": "Doodle (Creative Scala)",
        "repos": ["creativescala/doodle"],
        "focus": "`renderToTag` for the Scala.js SVG backend.",
    },
]


def search(query):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    items, page = [], 1
    while True:
        params = {"q": query, "sort": "created", "order": "desc", "per_page": 100, "page": page}
        url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as resp:
            data = json.load(resp)
        items += data["items"]
        if not data["items"] or len(items) >= data["total_count"]:
            return items
        page += 1


def repo_of(pr):
    return "/".join(pr["repository_url"].split("/")[-2:])


def clean_title(title, limit=72):
    # Drop project-specific tags such as "[p2]" so titles read cleanly in a table.
    title = re.sub(r"^\[[^\]]+\]\s*", "", title)
    title = re.sub(r"\s*\[[^\]]+\]$", "", title).replace("|", "\\|")
    return title if len(title) <= limit else title[: limit - 1].rstrip() + "…"


def pr_link(pr):
    return f'<a href="{pr["html_url"]}">#{pr["number"]}</a>'


def pulls_url(repos):
    query = f"is:pr author:{USER} " + " ".join(f"repo:{r}" for r in repos)
    return "https://github.com/pulls?q=" + urllib.parse.quote_plus(query)


def projects_table(merged, opened):
    rows = ["| Project | PRs | Focus |", "| --- | --- | --- |"]
    for p in PROJECTS:
        m = [pr for pr in merged if repo_of(pr) in p["repos"]]
        o = [pr for pr in opened if repo_of(pr) in p["repos"]]
        if not m and not o:
            continue
        if m:
            latest = max(m, key=lambda pr: pr["pull_request"]["merged_at"])
            note = f"Latest: {pr_link(latest)} — {clean_title(latest['title'])}"
        else:
            note = f"Open: {pr_link(o[0])} — {clean_title(o[0]['title'])}"
        counts = f"{len(m)} merged · {len(o)} open"
        rows.append(f"| [{p['name']}]({pulls_url(p['repos'])}) | {counts} | {p['focus']}<br><sub>{note}</sub> |")
    return "\n".join(rows)


def open_list(opened):
    if not opened:
        return "_None right now._"
    return "\n".join(
        f"- [{repo_of(pr)}#{pr['number']}]({pr['html_url']}) — {clean_title(pr['title'], 90)}" for pr in opened
    )


def main():
    upstream = f"is:pr author:{USER} -user:{USER}"
    merged = search(f"{upstream} is:merged")
    opened = search(f"{upstream} is:open")

    body = (
        TEMPLATE.read_text()
        .replace("{{MERGED_TOTAL}}", str(len(merged)))
        .replace("{{PROJECTS_TABLE}}", projects_table(merged, opened))
        .replace("{{OPEN_PRS}}", open_list(opened))
    )

    # Leave the file alone when only the timestamp would change.
    if README.exists():
        old = UPDATED_RE.sub("", README.read_text())
        if old == UPDATED_RE.sub("", HEADER + body.replace("{{UPDATED}}", "")):
            print("README unchanged")
            return

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    README.write_text(HEADER + body.replace("{{UPDATED}}", stamp))
    print("README updated")


if __name__ == "__main__":
    main()
