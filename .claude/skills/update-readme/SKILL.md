---
name: update-readme
description: Keeps the root README.md of this repo (3pc-skills) accurate and well-structured as the repo evolves — not just the skills table, the whole document. Use this whenever the user asks to "update the readme", "review the readme", "does the readme need updating", "keep the readme in sync", wants to add/reword a README section, or has just added/removed/renamed a skill under skills/ and the README needs to catch up. Always run this after any change to skills/ so the README doesn't go stale, and reach for it any time the README itself feels out of date.
---

# Update README

The README is the front door to this skills directory — it's what someone sees first on
GitHub before they open any individual skill. This skill has two parts: a mechanical
refresh of the skills listing (deterministic, script-driven), and a broader review of the
rest of the document against README best practices (judgment-driven, using the existing
README as the template for tone and structure).

## Step 1: Regenerate the skills table (this repo specifically)

In *this* repo (3pc-skills), the table of skills is fully derivable from each skill's
`SKILL.md` frontmatter (`name`, `description`) plus the repo's GitHub remote — there's no
judgment call in it, so let a script do it rather than hand-editing rows or retyping
links:

```bash
python3 .claude/skills/update-readme/scripts/generate_readme.py
```

It rewrites everything from the `## Skills` heading onward and leaves everything above
that heading untouched. Run `git diff README.md` afterward to see exactly what changed —
which skills were added, removed, or reworded — that diff is useful input for Step 2.
(This step is specific to this repo's structure — if you're applying this skill somewhere
without an equivalent mechanically-derivable listing, skip straight to Step 2.)

## Step 2: Review the rest of the README (works in any project)

This is the general-purpose part of the skill, not tied to 3pc-skills specifically. A
fixed checklist of "every README needs sections X, Y, Z" doesn't hold up across different
projects, so instead follow the process in
[references/readme-best-practices.md](references/readme-best-practices.md): scan the
actual repo (code, directory structure, config files like `LICENSE` or CI config) rather
than assuming, verify every existing claim in the README against what you find, remove
what's stale before adding anything new, and only add a section when something concrete in
the repo actually backs it — never speculatively.

Two things matter most in how you apply this:

- **Match the voice and structure already in the document** rather than imposing an
  outside idea of a "correct" README format.
- **Confirm structural changes with the user before finalizing them** — rewording the
  intro, adding/removing a section, or shifting tone are judgment calls, so propose the
  specific change and show it rather than silently rewriting prose. (The mechanical table
  refresh in Step 1 doesn't need this — there's no judgment call in it.)

If something about the project's conventions genuinely isn't answerable by scanning the
repo (e.g. who the README is actually for, or how strict to be about scope), ask the user
directly instead of guessing — a couple of targeted questions beats writing down an
invented convention as if it were established.
