---
name: update-readme
description: Update and improve a project's README.md by reading the actual codebase, comparing it against the Awesome README list (https://github.com/matiassingers/awesome-readme), and iterating conversationally with the user before touching any files. Use this skill whenever the user asks to update, improve, rewrite, polish, or review their README, wants feedback on how their project reads to newcomers, or wants their project's GitHub presentation to look more professional — even if they don't say the word "README" but describe wanting better docs, onboarding, or first impressions for their repo. Also use it when a user shares a project and asks something like "does this explain itself well" or "would people know how to use this."
---

# Update README

Help a user turn their project's README into something accurate, legible, and
genuinely useful to the people who land on it — not by pasting a generic
template over it, but by reading their actual code and comparing it against a
real example that does the job well.

The whole point of this skill is accuracy plus concrete inspiration. A README
that confidently describes a feature that no longer exists is worse than no
README. A README copied from a template that doesn't fit the project's genre
(a serious CLI tool doesn't need the same treatment as a playful side
project) misses its audience. Do the reading before proposing anything.

## Workflow

### 1. Scope the scan

Before reading anything, ask the user whether they want a **light scan** or a
**deep scan**, unless they've already told you:

- **Light scan** — package manifest (`package.json`, `pyproject.toml`,
  `Cargo.toml`, `go.mod`, etc.), the top two or three levels of the folder
  structure, and entry-point files. Enough to describe what the project is
  and roughly how it's organized. Fast, good for a first pass or a small
  project.
- **Deep scan** — everything in light scan, plus actually reading the
  primary source files, CLI help output, exported functions/classes, and
  tests. This is what lets you verify that usage examples and feature claims
  in the README still match what the code does today, which is usually the
  most valuable thing you can offer — READMEs rot quietly as code changes
  and nobody remembers to update the docs.

If the project is small, deep scan is usually cheap enough to just do. If it's
large, the tradeoff is real — say so and let the user decide.

### 2. Read the codebase

Do the scan at the depth you agreed on. You're building a picture of: what
the project actually does, who it's for (library consumed by other
developers? CLI end-users run directly? a web app? an internal tool?), how
someone installs and runs it, and what's genuinely notable or differentiated
about it.

### 3. Read the existing README

If one exists, note:
- What sections it has and what it's missing (see
  [references/readme-checklist.md](references/readme-checklist.md) for
  common sections and what each is for — not a mandatory checklist, a menu).
- Anything that contradicts what you found in the codebase (renamed
  commands, removed features, outdated install instructions, broken example
  code).
- Whether the tone and depth match the audience you identified in step 2.

If there's no README yet, treat this as a from-scratch draft and say so.

### 4. Find a comparable example from Awesome README

This is what makes the suggestions concrete instead of generic advice.

1. Fetch the Awesome README list itself:
   `https://github.com/matiassingers/awesome-readme`
2. Figure out what category the user's project fits — CLI tool, library or
   package, web app, game, design resource, GitHub profile, etc. — and what
   language/ecosystem it's in.
3. Pick one entry from the list's Examples section that's the closest match.
   If two are genuinely close, it's fine to pick two, but don't default to
   more than that — the point is a focused comparison, not a survey.
4. Fetch that project's actual README (follow the link into its repo).
5. Read it with a specific question in mind: *what choices is this README
   making that serve its audience, and would those same choices serve this
   user's project?* Look past the surface ("it has badges") to the reasoning
   ("the install command is the very first thing after the title, because
   this is a CLI tool and that's the first thing a user needs"). Note 2-4
   concrete, specific techniques worth borrowing — not a generic "add
   badges and a table of contents."

### 5. Share findings before writing anything

Tell the user, in plain language:
- What's missing or stale in their current README, tied to specific
  evidence from the codebase (not just "this section feels thin").
- Which project you picked from Awesome README as a comparison and why it's
  a reasonable match.
- The 2-4 specific techniques worth borrowing from it.

Ask what they want to prioritize. Some users want a full rewrite, others just
want the install section fixed. Let them steer.

### 6. Draft revisions conversationally

Propose changes in the chat as markdown — section by section, or as a full
draft, whichever fits the scope of change the user wants. This is a
back-and-forth, not a one-shot delivery: show a draft, get reactions, adjust.
Do not write to the actual README file yet.

Resist the urge to over-template. If the reference example uses a demo gif,
badges, and a comparison table, that's because those served *its* audience —
not because every README needs them. Carry over the underlying reasoning
(what does a first-time visitor need to see, in what order, to understand
and try this project?), not the literal section list.

### 7. Write only once approved

Once the user signs off on a draft, write or edit the real README.md. If
changes are substantial, it's worth summarizing what changed and why in your
final message, so the user has a clear record even after the conversation
scrolls away.

## Notes

- Never invent features, commands, or usage examples that don't exist in the
  code. If you're not sure something still works as described, say so and
  ask, rather than guessing.
- Don't force stylistic elements (emojis, badges, gifs) onto a project whose
  existing tone doesn't fit them. Match the audience and genre of the
  project, which you should already have a read on from steps 2-3.
