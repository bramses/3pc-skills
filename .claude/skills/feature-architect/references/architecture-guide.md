# Architecture guide: what each mechanism can and can't do

This is the reference `feature-architect` consults when recommending how to build
something. It exists because of the subway skill: it was built twice (once scraping
HTML, once hitting the Transiter API directly from a bundled script), shipped, and
then pulled — both versions relied on a skill script making its own outbound network
call, which works in Claude Code but is blocked in the Claude Desktop/claude.ai skill
sandbox. That fact was discovered only after two full builds. The point of this doc
is to surface that kind of constraint *before* anything gets built, not after.

Nothing here is generic advice — every entry states a concrete capability or limit,
because vague answers ("skills are for domain expertise") are exactly what let the
subway problem slip through twice.

## Skill

Auto-invoked by Claude matching the request against `SKILL.md` frontmatter
`description` — no manual trigger needed. Bundles instructions, templates, and
optionally scripts (Python/Bash) under the skill's folder.

- **Claude Code**: bundled scripts run as real subprocesses with real network
  access. A script can call an external API directly (this is how subway v1 and v2
  worked, and it's genuinely fine *if Code is the only target surface*).
- **Claude Desktop / claude.ai**: bundled scripts execute in a sandbox that
  **blocks arbitrary outbound network requests**. Only built-in tools (the model's
  own web fetch/search) and *connected MCP servers* have real network access there.
  A skill script that calls `requests.get(...)` or similar will fail silently or
  error out for every user on this surface — this is the exact, confirmed reason
  the subway skill was removed (see `git show 8670d02` in this repo).
- **Implication**: if a skill needs live external data and must work on
  Desktop/claude.ai, it cannot bundle a script that hits the API itself. It needs
  either an MCP server the user has connected, or to route the request through the
  model's own built-in fetch capability (asking Claude to fetch a URL directly,
  not via a bundled script) — see `update-readme`'s own skill in this repo, which
  works everywhere specifically because it never bundles a network-calling script.
- **Token cost**: the `description` frontmatter is scanned for every request
  (cheap, keep it tight but complete). The body and any `references/*` files are
  only loaded into context once the skill actually triggers — so push detail,
  examples, and rarely-needed material into `references/`, and keep `SKILL.md`
  itself short. A skill with a 300-line `SKILL.md` and no references costs tokens
  on every invocation whether or not that detail is needed.

## Slash command

A markdown file under `.claude/commands/` (project) or `~/.claude/commands/`
(personal), invoked only when the user types `/name`.

- No auto-invocation — if the user forgets the command exists, it never fires.
- Cheapest mechanism token-wise: no frontmatter scanning overhead on unrelated
  requests, just the prompt text when actually run.
- No isolated context, no bundled scripts of its own.
- Right choice when: the user is fine typing a specific command, the task is a
  single repeatable prompt, and it doesn't need auto-detection or bundled assets.

## Subagent

A specialized assistant with its own system prompt and (usually) its own isolated
context window, spawned by the main agent via the `Agent`/`Task` mechanism.

- Full separate token cost per spawn — the subagent gets its own context, does its
  work, and returns a summary; that summary synthesis plus the subagent's own
  token usage is real cost on top of the main conversation.
- Good for: heavy research/exploration that would otherwise flood the main
  thread's context, or work that benefits from a different system prompt/tool
  scope than the main conversation.
- Bad for: anything cheap or quick — the isolation overhead isn't worth it for a
  simple lookup or a short transformation.
- Not something workshop clients "install" — this is a technique used *within* a
  Claude Code session, not a distributable artifact like a skill or plugin.

## MCP server

A separately configured connection (`.mcp.json` project-level or client-level
config) giving Claude live, authenticated access to an external system
(GitHub, a database, Slack, a transit API, etc.).

- **The only way to get real, live network access on Desktop/claude.ai.** If a
  feature must fetch live data on that surface and no MCP exists for the target
  API, that is a genuine blocker — not something a bundled script can route
  around, per the sandbox restriction described above.
- Requires setup by whoever runs it: credentials, install, connection. A skill
  cannot silently bundle an MCP server and have it "just work" for a
  non-technical workshop attendee with zero setup — surface this requirement
  explicitly rather than assuming it away.
- No caching by default — every call is a live round trip, which has its own
  latency/rate-limit considerations separate from token cost.

## Plugin

A single-install bundle combining multiple commands, subagents, MCP servers, and
hooks (`.claude-plugin/plugin.json` manifest, installed via `/plugin install`).

- Right altitude for: a full repeatable workflow with several moving parts,
  distributed as one unit to a team (e.g. "everything a new client engagement
  needs" — commands + an MCP connection + a review subagent, all at once).
- Overkill for: a single capability. If the feature is "one skill," packaging it
  as a plugin adds manifest/versioning overhead for no benefit.
- Still subject to the same per-component constraints above — bundling a
  network-calling script inside a plugin's skill component doesn't change the
  Desktop/claude.ai sandbox behavior.

## Hook

Shell commands wired to Claude Code lifecycle events (`PreToolUse`, `PostToolUse`,
`Stop`, etc.) via `.claude/settings.json`.

- Local automation tied to the maintainer's own Claude Code environment — not
  something handed to a workshop client as a deliverable.
- Should be fast (sub-second) and non-interactive; not a place for a feature with
  real logic or user-facing behavior.
- Right choice for: auto-formatting, validation gates, notifications tied to the
  maintainer's own workflow, not client-facing functionality.

## Memory / CLAUDE.md

Durable, automatically-loaded context (project `CLAUDE.md`, user memory, this
skill's own `references/`) — not "invoked," always present once loaded.

- Right for: stable facts, preferences, standing conventions.
- Wrong for: live/changing data (that's MCP) or one-off capabilities (that's a
  skill or command) — memory doesn't "do" anything, it just informs.

## Decision tree

Ask, in order:

1. **Does this need live/external data at request time?**
   - No → it's a Skill (reusable instructions/templates) or a Slash command
     (single manual prompt), decided by question 4.
   - Yes → go to 2.

2. **What surface(s) must it work on?** (ask explicitly — don't assume Code)
   - Claude Code only → a skill can bundle a script that calls the API directly.
     Fine, this is what subway v1/v2 did and it would still work today *if Code
     were the only target*.
   - Desktop/claude.ai (at all) → a bundled script calling the API directly will
     not work. Check: is there already a connected MCP server for this API? If
     yes, build the skill/command around that MCP's tools. If no, that's a
     blocker to name out loud now — either scope the feature to Code-only, find/
     build an MCP for it, or restructure the request as something the model's
     built-in fetch can handle directly.
   - Both, varying by feature → treat each feature independently; don't assume
     the previous feature's answer carries over.

3. **Does it need credentials or a standing connection?**
   - Yes → MCP server (with the setup burden on whoever runs it), not a script
     bundled inside a skill.

4. **Is it a one-off the user is willing to type, or should Claude auto-detect
   it?**
   - One-off, user-typed → Slash command.
   - Should trigger automatically from context → Skill.

5. **Does it bundle several distinct components (multiple commands + an MCP +
   hooks) meant for one-command team distribution?**
   - Yes → Plugin, wrapping the components decided above.
   - No → just ship the Skill/Command/MCP-integration on its own.

6. **Does it need heavy isolated research/exploration that shouldn't pollute the
   main conversation?**
   - Yes → consider a Subagent for that sub-step specifically (this is a
     technique used inside a build, not an alternative to the choices above).
