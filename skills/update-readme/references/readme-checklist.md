# README elements — a menu, not a checklist

This is a reference for spotting gaps, not a template to fill in top to
bottom. A good README includes what its specific audience needs and skips
the rest. Use this to notice what might be missing or worth reconsidering,
then decide with the user whether it's actually worth adding.

## Near the top (what a first-time visitor sees without scrolling)

- **Title and one-line description** — what the project is, in plain
  language. Should answer "what is this" before anything else.
- **Badges** — build status, version, license, etc. Useful signal for
  libraries and open-source infrastructure that other developers will
  depend on. Often noise on a small personal project or internal tool —
  don't add them reflexively.
- **Demo (screenshot, gif, or short example output)** — most valuable for
  anything visual (UI, CLI with interesting output, games). Less useful for
  a library whose value is in its API.
- **Quick-start / install snippet** — the single command or two that gets
  someone running. For CLI tools and libraries, this is often the single
  highest-value thing to get right, and the first thing an impatient reader
  looks for.

## Body

- **Usage examples** — real, runnable examples, ideally the same shape as
  what a user will actually write. This is the section most likely to go
  stale as APIs change — worth double-checking against the actual code.
- **Configuration / options** — if the project has meaningful configuration
  surface (flags, env vars, config file), document the common cases; link
  out to full reference docs for the rest rather than dumping everything
  here.
- **Why / motivation** — for projects with alternatives already in the
  space, a short note on what problem this solves or how it differs helps a
  reader decide if it's relevant to them without reading the whole thing.
- **Architecture / how it works** — worth including when understanding the
  internals materially helps users or contributors; skip it for simple
  projects where it'd just be restating the code.

## Toward the bottom

- **Contributing** — how to set up a dev environment, run tests, submit
  changes. Matters for projects that want or expect outside contributions;
  skip for personal or closed projects.
- **Tests** — how to run them, if relevant to contributors.
- **License** — include if the project has one; don't invent one.
- **Acknowledgments / related projects** — optional, but a nice signal of
  good faith and helps readers who land here but actually wanted something
  adjacent.
- **Contact / support** — how to reach maintainers or file issues, useful
  once a project has users beyond its author.

## Judgment calls worth making explicitly with the user

- **Audience**: are readers mostly other developers evaluating whether to
  depend on this, end-users who just want to run it, or contributors who
  need to build it? Different audiences want different things first.
- **Tone**: match the project's existing voice. A playful side project
  doesn't need corporate badges-and-TOC treatment; a library other teams
  depend on probably benefits from one.
- **Length**: a long, thorough README isn't automatically better. If detail
  belongs in a docs site or wiki, the README should point there rather than
  duplicate it.
