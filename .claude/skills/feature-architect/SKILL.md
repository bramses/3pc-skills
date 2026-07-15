---
name: feature-architect
description: Decide how a new workshop-sourced feature idea should actually be built — as a skill, plugin, slash command, subagent, MCP integration, or hook — before any scaffolding starts. Use this whenever the user is starting a new feature/tool and asks things like "should this be a plugin or a skill," "what should we build this as," "how do we make this work," or describes a new idea from a workshop/client and wants help deciding the shape of it. Also trigger when the user is about to build something that needs live external data or an API, since that's the case most likely to hit a hard platform constraint. Do not use this for actually writing a skill once the shape is already decided — hand off to skill-creator for that.
---

# Feature architect

This skill exists because of the subway skill: it was built twice, shipped, and
then pulled, because both versions bundled a script that made its own outbound
network call — which works in Claude Code but is silently blocked in the Claude
Desktop/claude.ai skill sandbox. That constraint was only discovered after two full
builds. This skill's job is to surface constraints like that *before* the user
commits to building anything, not after.

Read [references/architecture-guide.md](references/architecture-guide.md) before
recommending anything — it has the actual capability/constraint matrix and the
decision tree. Don't recommend a mechanism from memory or general Claude knowledge;
this repo has already been burned by a plausible-sounding but wrong assumption
("bundle a script that calls the API" seemed reasonable until it wasn't).

## Flow

### 1. Interview

Ask about the feature idea — don't assume answers, especially not surface:

- What does it actually need to do?
- Does it need live/external data (an API, a database, anything that changes
  after the skill ships)?
- Who runs it, and on which surface(s): Claude Code, Claude Desktop, claude.ai,
  or a mix? Ask explicitly every time — this repo's features have landed on
  different surfaces depending on the feature, so never assume Code-only.
- Is this a one-off for personal/dev use, or something handed to workshop
  attendees or clients?
- Does it need credentials or a standing connection to something?
- Is this one capability, or several things that belong bundled together
  (multiple commands, an MCP connection, hooks, all as one install)?

### 2. Recommend

Walk the decision tree in `references/architecture-guide.md` using the answers
above. Name the mechanism (skill / slash command / subagent / MCP integration /
plugin / hook / memory) — and if different surfaces need different builds, say so
rather than forcing one answer.

### 3. State constraints and gate — do not skip this

Before discussing any scaffolding, state plainly and specifically:
- What this mechanism **can** do, given the answers above.
- What it **cannot** do — especially any hard platform constraint (e.g. "a
  bundled script in this skill will not be able to reach the network on Desktop/
  claude.ai; without a connected MCP for this API, it'll silently break there the
  same way the subway skill did").
- Any missing prerequisite (e.g. no MCP server exists yet for the API this needs).

Then **ask the user to explicitly confirm they understand these constraints**
before proceeding. Do not move to building, scaffolding, or handing off to
skill-creator until they've done so. If they push back or want to proceed despite
a stated blocker, make sure the specific tradeoff they're accepting is said out
loud in the conversation, not just implied.

### 4. Note token-cost tradeoffs

Briefly state the cost profile of the chosen approach using
`references/architecture-guide.md`'s per-mechanism notes (e.g. a subagent costs a
full separate context per spawn; a slash command is nearly free but requires the
user to type it; a skill's `SKILL.md` should stay short with detail pushed into
`references/` loaded only on trigger).

### 5. Hand off — don't rebuild scaffolding here

Once the user has confirmed the constraints, this skill's job is done. For
actually building:
- Skill or plugin scaffolding → hand off to the `skill-creator` skill.
- Slash command → just write the markdown file under `.claude/commands/`.
- Hook → edit `.claude/settings.json` directly (see the `update-config` skill).
- MCP integration → confirm what's already connected before assuming a new one
  needs to be stood up.

Don't reimplement any of that logic inside this skill — it recommends and gates,
it doesn't build.
