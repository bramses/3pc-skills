#!/usr/bin/env python3
"""Regenerate the '## Skills' table in the repo root README.md from skills/*/SKILL.md."""
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILLS_DIR = REPO_ROOT / "skills"
README_PATH = REPO_ROOT / "README.md"
SECTION_HEADING = "## Skills"


def get_repo_and_branch() -> tuple[str, str]:
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    match = re.search(r"github\.com[:/](?P<slug>[^/]+/[^/]+?)(\.git)?$", remote)
    if not match:
        raise SystemExit(f"Could not parse a GitHub repo slug from remote URL: {remote}")
    slug = match.group("slug")

    branch = subprocess.run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"], cwd=REPO_ROOT, capture_output=True, text=True
    ).stdout.strip()
    branch_name = branch.rsplit("/", 1)[-1] if branch else "main"
    return slug, branch_name or "main"


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValueError(f"No frontmatter found in {skill_md}")
    fields: dict[str, str] = {}
    key = None
    for line in match.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if kv:
            key = kv.group(1)
            fields[key] = kv.group(2).strip()
        elif key and line.strip():
            fields[key] += " " + line.strip()
    return fields


def summarize(description: str, max_len: int = 220) -> str:
    # Drop leading "Use this/when..." framing where a plainer opening sentence exists later,
    # then trim to the first sentence(s) that fit within max_len.
    sentences = re.split(r"(?<=[.!?])\s+", description.strip())
    summary = ""
    for sentence in sentences:
        candidate = (summary + " " + sentence).strip() if summary else sentence
        if len(candidate) > max_len and summary:
            break
        summary = candidate
        if len(summary) >= max_len:
            break
    return summary.strip()


def collect_skills(repo_slug: str, branch: str) -> list[dict[str, str]]:
    rows = []
    for skill_dir in sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        fields = parse_frontmatter(skill_md)
        name = fields.get("name", skill_dir.name)
        description = summarize(fields.get("description", ""))
        link = f"https://github.com/{repo_slug}/tree/{branch}/skills/{skill_dir.name}"
        rows.append({"name": name, "link": link, "description": description})
    return rows


def render_table(rows: list[dict[str, str]]) -> str:
    lines = [SECTION_HEADING, "", "| Skill | What it does |", "| --- | --- |"]
    for row in rows:
        lines.append(f"| [{row['name']}]({row['link']}) | {row['description']} |")
    return "\n".join(lines) + "\n"


def update_readme(rows: list[dict[str, str]]) -> None:
    if not README_PATH.exists():
        raise SystemExit(f"{README_PATH} does not exist")
    content = README_PATH.read_text()
    table = render_table(rows)

    if SECTION_HEADING in content:
        before = content.split(SECTION_HEADING, 1)[0].rstrip() + "\n\n"
        new_content = before + table
    else:
        new_content = content.rstrip() + "\n\n" + table

    README_PATH.write_text(new_content)


def main() -> None:
    if not SKILLS_DIR.is_dir():
        raise SystemExit(f"No skills/ directory found at {SKILLS_DIR}")
    repo_slug, branch = get_repo_and_branch()
    rows = collect_skills(repo_slug, branch)
    if not rows:
        print("No skills found under skills/ — leaving README untouched.", file=sys.stderr)
        return
    update_readme(rows)
    print(f"Updated {README_PATH} with {len(rows)} skill(s).")


if __name__ == "__main__":
    main()
