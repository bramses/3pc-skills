# README best practices (portable across projects)

This is an algorithm, not a checklist of sections to fill in. A fixed list of "every
README should have X, Y, Z" doesn't survive contact with a different project — a skills
directory, a CLI tool, and a library need different things. What generalizes is the
*process* for deciding what belongs, applied fresh to whatever repo you're actually in.

## The process

1. **Scan the repo before claiming anything about it.** Don't infer what the README
   should say from what READMEs usually say — look at the actual code, directory
   structure, config files (`LICENSE`, CI config, `package.json`/`pyproject.toml`, test
   directories, a `CONTRIBUTING.md`) to see what's really there. A section is justified by
   something concrete in the repo, not by convention.
2. **Verify every existing claim in the README against that scan.** Treat the current
   README as a set of claims to check, not ground truth: does the intro still describe
   what the repo does, do the linked paths still exist, does a described workflow
   ("skills are reviewed before merging", "run `npm test`") actually reflect how the repo
   works today?
3. **Remove what's stale or unused before adding anything new.** Dead sections, links to
   deleted files, descriptions of a workflow that changed — clear these out first. A
   README that accurately describes less is better than one that inaccurately describes
   more.
4. **Add a section only when something concrete in the repo backs it right now** — not
   because it's common in other READMEs, and not preemptively for where the project might
   go. Examples: add a license section once a `LICENSE` file exists; add a
   contributing/how-to section once there's an actual repeatable process to document;
   add install instructions once there's something to actually install. If you can't point
   to the concrete thing that backs a section, don't add it yet.
5. **Match the voice and structure already in the document.** Don't introduce a new tone
   or format partway through — if the rest of the README is written a certain way, follow
   it rather than imposing a "correct" style from outside.
6. **Confirm structural changes with the user before finalizing them.** Rewording the
   intro, adding or removing a section, or changing the voice are judgment calls — propose
   the specific change and show it, rather than silently rewriting prose. (Purely
   mechanical refreshes, like regenerating a table from source files, don't need this —
   there's no judgment call to confirm.)

## When you genuinely don't know enough about the project's conventions

If scanning the repo doesn't answer a question — e.g. it's ambiguous whether the README
is meant for external users or just the maintainer, or there's no signal on how strict to
be about scope — ask the user directly rather than guessing. A couple of targeted
questions beats inventing a convention and writing it down as if it were established.
