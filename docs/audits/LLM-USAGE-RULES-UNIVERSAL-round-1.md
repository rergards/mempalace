# LLM Usage Rules — Universal & LLM-Agnostic Revision

**Goal:** make `docs/LLM_USAGE_RULES.md` effective for *any* MCP-capable LLM agent (Claude Code, Codex, Cursor, Windsurf, Zed, Continue.dev, Aider, future agents) without degrading Claude Code behaviour. Outcome: an assistant that reliably calls the right mempalace tool at the right time with the right payload, regardless of host.

---

## 1. Existing State (as of 2026-04-21)

### 1.1 Files in scope

| File | Role |
|------|------|
| `docs/LLM_USAGE_RULES.md` (88 lines) | Canonical usage-rules block. Humans/agents paste the section below `# mempalace-code — Usage Rules` into their agent's instructions. |
| `docs/AGENT_INSTALL.md` §7 (lines 553–646) | Install runbook embeds the same block inline and appends it to `CLAUDE.md` automatically. |
| `docs/AGENT_INSTALL.md` §5.3 | Points at "MCP + usage rules" as the universal auto-save mechanism (replaces Claude-specific hooks). |
| `README.md` → MCP Server section | Lists 27 MCP tools (source-of-truth count referenced from §7 and the End State table). |
| `hooks/README.md` | Legacy Claude Code auto-save hooks; redundant when rules are in place. |

### 1.2 Current usage-rules block — structure

```
# mempalace-code — Usage Rules
## Core Concepts          (Wings / Rooms / Drawers / KG — 4 bullets)
## When to Search         (mandatory-before triggers, 2–3 phrasings)
## When to Write          (triggers, "do not write" list, content rules)
## Wing/Room Conventions  (3-row table, list_rooms reminder)
## Knowledge Graph        (change-over-time, invalidate-before-replace)
## Agent Diary            (session wrap-up, agent_name example)
```

Length: ~59 lines of actual content. Dense.

### 1.3 Distribution table (lines 5–26)

Covers Claude Code (global/project), Claude Desktop, Codex CLI, Cursor, Windsurf, "Other MCP clients". One-liner: `cat docs/LLM_USAGE_RULES.md >> ~/.claude/CLAUDE.md`. AGENT_INSTALL.md §7 performs this automatically for Claude Code only.

### 1.4 Tool inventory assumed by the rules

Rules explicitly name 5 tools:

- `mempalace_search`
- `mempalace_add_drawer`
- `mempalace_kg_query` / `mempalace_kg_invalidate` / `mempalace_kg_*`
- `mempalace_list_rooms`
- `mempalace_diary_write`

The MCP server actually exposes **28 tools** (verified from `mempalace/mcp_server.py` tool registry). Unnamed in the rules — silently ignored by many agents:

```
mempalace_status            mempalace_list_wings          mempalace_get_taxonomy
mempalace_kg_add            mempalace_kg_timeline         mempalace_kg_stats
mempalace_find_implementations  mempalace_find_references
mempalace_show_project_graph    mempalace_show_type_dependencies
mempalace_explain_subsystem     mempalace_extract_reusable
mempalace_traverse              mempalace_find_tunnels    mempalace_graph_stats
mempalace_code_search           mempalace_file_context
mempalace_check_duplicate       mempalace_delete_drawer   mempalace_delete_wing
mempalace_diary_read            mempalace_mine
```

Agents don't reach for tools they aren't told about. Code-graph, subsystem explanation, and duplicate-check tools are almost never invoked because the rules don't mention them.

---

## 2. Gaps & Failure Modes Observed

### 2.1 Claude-centric framing leaks into "universal" content

- `agent_name` example says only `"claude-code"` — a Codex or Cursor reader will copy that verbatim and all diary entries end up attributed to Claude.
- Distribution table lists Claude Code first; everything else reads as an afterthought.
- No mention of MCP discovery protocol — agents that introspect tool schemas at startup (Cursor, Zed, Continue) need schema hints more than prose.

### 2.2 Missing decision trees

Current rules tell the agent *when* to search and *when* to write, but not *which tool* to use when multiple apply:

- "Past decision" → drawer? diary? KG? Three valid choices, no guidance.
- "Current version of X" → drawer or KG? The "change over time" heuristic is correct but not stated as a routing rule.
- "Search before acting" — the rule says search first, but doesn't say `mempalace_search` vs `mempalace_code_search` vs `mempalace_kg_query` vs `mempalace_traverse`. An agent given 28 tools defaults to the first plausible match, usually `mempalace_search`.

### 2.3 No query-craft guidance

"Try 2–3 phrasings" is there but abstract. Agents do not naturally know:

- Semantic search rewards **declarative phrases** ("why we chose Postgres") over keywords ("postgres choice").
- Proper-noun spelling matters (`wh40kdh2calc_planner` vs `DH2`).
- Scoping with `wing=` parameter cuts false positives dramatically but is undocumented in the rules.

### 2.4 No content-shape guidance for drawers

"Verbatim, include context, one topic" is right but doesn't translate to a template. Result: inconsistent drawer formats across sessions, weaker semantic retrieval over time.

### 2.5 No anti-pattern catalogue

"Do not write routine code changes" is one item. Missing:

- Don't store secrets / tokens / credentials
- Don't store ephemeral task state (that's what the host's todo-list is for)
- Don't store giant file contents — link back to the file path
- Don't create a new wing when an existing one fits (wings proliferate otherwise)
- Don't duplicate KG facts with drawers when both could apply — KG wins for temporal

### 2.6 No "how to handle a search miss" rule

Agents either give up or invent answers. Rule should say: on repeated miss, fall back to the host's code/file tools, then consider whether the gap is worth writing a drawer for after the task completes.

### 2.7 Diary vs drawer ambiguity

Both are written "at end of significant sessions" per the current rules. In practice:
- **Diary** = agent-first-person session summary, scoped by `agent_name`, read on next session start.
- **Drawer** = decision/context artefact, shared across agents, retrieved by semantic search.

This distinction is not in the rules.

### 2.8 Host-specific parts mixed with universal parts

The canonical block (§7 of AGENT_INSTALL.md) is meant to be universal, but the surrounding install flow references `claude mcp list` and writes only to `CLAUDE.md`. Codex/Cursor users who follow AGENT_INSTALL.md get MCP wiring (§5.2) but never see the rules injected — §7 targets `CLAUDE.md` only.

---

## 3. Proposed Revised Rules (LLM-Agnostic)

Drop-in replacement for `docs/LLM_USAGE_RULES.md` below the distribution table. Edits also flow into `AGENT_INSTALL.md` §7.3 and `README.md`.

Design principles:

1. **Tool-first organisation.** Each section is headed by the tool it governs, so an agent skimming can map capability → rule directly.
2. **Decision tree up front.** One "which tool, when?" table replaces three scattered hints.
3. **Templates over prose.** Drawer shape, query shape, and KG triple shape are shown by example.
4. **Host-neutral examples.** `agent_name` uses a placeholder; no Claude/Codex name-dropping inside the rules.
5. **Anti-pattern list.** Explicit "never" list to counteract AI drift.
6. **Same length budget.** Target ≤ 120 lines so the block stays paste-friendly into any `*.md` or system prompt.

### 3.1 Proposed content

```markdown
# mempalace-code — Usage Rules

mempalace-code is a local semantic memory system exposed over MCP. Content is stored
verbatim in a vector database; no cloud, no API keys, no summarisation. These rules
teach an LLM agent *when* to call each MCP tool and *how* to shape the payload.

## Mental model

- **Wing** — a project or knowledge domain. One per repo, plus cross-project wings
  like `people` and `decisions`.
- **Room** — a topic within a wing (`backend`, `debugging`, `meetings`). Rooms are
  organisational; searches ignore them unless you scope explicitly.
- **Drawer** — a verbatim piece of content stored in a room. Persistent, shared across
  agents, retrieved by meaning.
- **Knowledge Graph (KG)** — entity-relationship triples with validity windows. Use
  for facts that evolve (versions, roles, statuses, deadlines).
- **Diary** — agent-scoped, first-person session log. Read on the next session to
  restore continuity; never shared with humans as authoritative reference.

## Routing: which tool, when?

| Task                                         | Primary tool                   | Fallback          |
|----------------------------------------------|--------------------------------|-------------------|
| "Have we discussed X before?"                | `mempalace_search`             | `mempalace_kg_query` |
| "What is the current value of X?"            | `mempalace_kg_query`           | `mempalace_search`   |
| "Find a function/class/file"                 | `mempalace_code_search`        | `mempalace_search`   |
| "Where is symbol Y defined or used?"         | `mempalace_find_implementations` / `mempalace_find_references` | `mempalace_code_search` |
| "Explain subsystem or module boundary"       | `mempalace_explain_subsystem`  | `mempalace_search`   |
| "Walk related nodes in the code graph"       | `mempalace_traverse`           | —                    |
| Save a decision / root cause / discussion    | `mempalace_add_drawer`         | —                    |
| Save/update a temporal fact                  | `mempalace_kg_invalidate` + `mempalace_kg_add` | —    |
| End-of-session continuity note (self-scoped) | `mempalace_diary_write`        | —                    |
| Verify palace is alive before relying on it  | `mempalace_status`             | —                    |

Default to `mempalace_search` only when no more specific tool applies.

## Search rules

Call `mempalace_search` **before** reading repo files, grepping, or planning, for:

- New feature requests — search the feature name and adjacent concepts.
- Bug investigations — search the symptom, then the suspected component.
- Questions about past decisions, people, timelines, or project history.
- Any topic plausibly discussed in a previous session.

Query craft:

- Prefer **declarative phrasing**: `"why we chose Postgres over MySQL"` beats
  `"postgres mysql decision"`.
- Use proper-noun spellings verbatim (project slugs, code names).
- Scope with `wing=<project_slug>` when the topic is clearly project-local; omit
  `wing` for cross-cutting questions (people, decisions, conventions).
- On a thin result (similarity < 0.5 or no hits), try 2–3 reformulations before
  giving up. If still empty, proceed with host tools and consider writing a drawer
  after the task, so the next agent finds it.

Skip search only for pure mechanical operations (run tests, format files, rename a
variable inside one file) where there is genuinely nothing to look up.

## Knowledge Graph rules

Use the KG for facts that **change over time** or need **exact-match lookup**:

- Version numbers, stack choices, ownership, statuses, deadlines, freezes.
- Good triples: `(myapp, uses, Postgres)`, `(mempalace-code, version, 3.0.0)`,
  `(team-ingest, owns, pipeline-etl)`.
- Bad for KG: code patterns, debugging notes, long prose — use a drawer.

Update protocol:

1. `mempalace_kg_query` to find the current triple.
2. `mempalace_kg_invalidate` the old one with today's date.
3. `mempalace_kg_add` the new one with a validity window.

Never let two triples for the same (subject, predicate) remain live.

## Drawer rules

Write a drawer after:

- A significant decision or architectural discussion (reasoning + rejected alternatives).
- Debugging a hard problem (root cause, not the surface symptom).
- Learning durable context about people, timelines, or project goals.
- Significant session wrap-up that others might need.

Do **not** write:

- Routine code changes — git log is authoritative.
- Content already in project files (READMEs, CLAUDE.md, BACKLOGs).
- Secrets, tokens, credentials, PII.
- Ephemeral task state — that belongs in the host's todo list.
- Giant file contents — reference the path instead.

Drawer shape (Markdown, ≤ ~60 lines):

```
# <topic in one line>

**Context:** who was involved, when, what triggered this.
**Decision / finding:** one or two sentences, direct.
**Why:** reasoning, tradeoffs, rejected alternatives.
**Impact:** what this changes going forward, who is affected.
**References:** file paths, PRs, issue IDs, related drawers.
```

Before writing, optionally call `mempalace_check_duplicate` with the proposed content;
the tool already rejects near-duplicates at 0.9 similarity, but explicit checks let
you merge rather than overwrite.

## Wing & room conventions

| Wing              | Use for                                              |
|-------------------|------------------------------------------------------|
| `<project_slug>`  | Project-specific knowledge. One wing per repo.       |
| `people`          | Facts about collaborators and stakeholders.          |
| `decisions`       | Cross-project architectural or process decisions.    |

Call `mempalace_list_wings` / `mempalace_list_rooms` before inventing new names.
Reuse existing rooms (`backend`, `frontend`, `architecture`, `debugging`, `meetings`,
`infrastructure`, `general`) unless a new topic genuinely warrants a new room.

## Diary rules

`mempalace_diary_write` creates an agent-scoped, first-person session record.

- Pass `agent_name` = the running agent's stable identity string (e.g. the host's
  agent ID). Never hardcode another agent's name.
- Write once at the end of a meaningful session — not per message.
- Content: what was attempted, what shipped, what remains, where you left off.
- Read with `mempalace_diary_read` at session start when continuity matters.

Diary ≠ drawer. Diary is for the agent's own next run; drawer is for the team.

## Maintenance

- Delete with `mempalace_delete_drawer` only when content is *wrong*. If facts
  evolved, add a new drawer and let history stand.
- Check `mempalace_status` at session start if you are about to rely heavily on
  memory; a stale or empty palace should change your plan.

## Never

- Never fabricate a tool call or invent tool names. If the tool is not in your MCP
  tool list, it is not available — fall back to host tools.
- Never store secrets, tokens, credentials, personal data.
- Never summarise or compress drawer content; store verbatim.
- Never create a new wing when an existing one fits.
- Never leave two live KG triples for the same (subject, predicate).
```

### 3.2 Secondary edits

1. **`docs/LLM_USAGE_RULES.md` header (lines 1–26).** Reorder the distribution table alphabetically by agent; drop the "Claude Code first" implicit ranking. Replace the `cat` one-liner with a neutral snippet and add equivalents for `~/.codex/AGENTS.md`, `.cursorrules`, `.windsurfrules`, `.continuerules`.
2. **`AGENT_INSTALL.md` §7.2.** Target file selection should branch on the agent detected during install, not hardcode `CLAUDE.md`. Minimum viable: if Codex was wired in §5.2, also offer `~/.codex/AGENTS.md`.
3. **`AGENT_INSTALL.md` §7.3.** Replace the inline block with a `<!-- source: docs/LLM_USAGE_RULES.md -->` marker plus an embed directive, so the two files cannot drift. Current state has them duplicated verbatim with a "keep in sync" comment — drift is inevitable.
4. **`README.md`** — add a one-paragraph "How to teach your agent to use mempalace" pointer to `LLM_USAGE_RULES.md` near the MCP tool list.

### 3.3 Non-goals

- No tool API changes. This is pure documentation and prompt engineering.
- No breaking changes to existing CLAUDE.md installations — the new block is a strict superset of the old one in information content.
- No per-agent rule variants. One block, universal.

---

## 4. Open Questions for Review

1. Is the 120-line budget the right target? Claude Code reads everything in CLAUDE.md on every turn; over-long rules tax context. Codex (`AGENTS.md`) has similar cost. Would a short "must-read" core + linked "how-to" appendix work better?
2. Should the "Routing" table be the very first section? Argument for: agents that skim grab the routing first. Against: mental-model grounding is needed before routes make sense.
3. Should drawer template be prescribed at all? Prescribing increases consistency but risks agents rejecting content that doesn't fit the template. Suggestion: "recommended" not "required."
4. Agent-name handling for diary: should the rules name an env var (`MEMPALACE_AGENT_NAME`) that hosts set, so the agent doesn't have to guess its own identity? Low effort, big payoff for correctness.
5. Anti-patterns: should "Never store secrets" warrant a hard guard (scan the payload before `add_drawer`) or is documentation enough?
6. Is the taxonomy (`people`, `decisions`, `<project_slug>`) right as a global convention, or should each team pick their own? Fixing it reduces decision fatigue; flexibility means less adoption friction.

---

## 5. What to Expect From Review

Codex should evaluate:

- **Clarity** — would a fresh agent (no prior mempalace exposure) know what to do?
- **Actionability** — are the rules imperative enough to drive tool calls, or do they read like aspirational prose?
- **Coverage vs. length** — does the proposed block trade length for the right coverage?
- **LLM-agnosticism** — are there any remaining Claude-isms, Codex-isms, or assumptions about host capabilities?
- **Anti-patterns** — is anything in the "Never" list wrong or missing?
- **Routing table** — is the tool→task mapping right for a zero-shot reader?

Return concrete line-level edits where possible.

---

## 6. Codex Review (2026-04-21, gpt-5 default)

- **Routing table is materially wrong on code-graph rows.** `mempalace_find_implementations` is .NET interface-only; `mempalace_find_references` is a type/project KG lookup; `mempalace_traverse` walks palace rooms, not the code graph (see `mempalace/mcp_server.py:1195–1357`). Replace those rows with explicit entries for `mempalace_code_search`, `mempalace_file_context`, `mempalace_show_project_graph`, `mempalace_show_type_dependencies`. Keep `mempalace_traverse` only for cross-room palace navigation.
- **`mempalace_explain_subsystem` overclaimed.** Good for "how does X work?", not "module boundary." Add a separate row for `mempalace_extract_reusable` for extraction/boundary questions (`mcp_server.py:1311–1339`).
- **Block exceeds the 120-line budget** (~149 lines). Trim hard: move query-craft detail, drawer template, and maintenance/destructive-tool notes into an appendix. Zero-shot agents need a short core, not a mini-manual.
- **"Call `mempalace_search` before reading repo files…" is too absolute** — causes pointless tool churn in empty palaces. Change to "before substantial repo exploration when prior context could plausibly exist."
- **Drop the `similarity < 0.5` magic number.** Say "on low-confidence or empty results."
- **Host-assumption leaks remain.** "host's todo list" and "host's stable agent ID" are not universal. Use "task tracker/scratchpad" and recommend a configured `MEMPALACE_AGENT_NAME` instead of guessing.
- **Diary section not actionable** — `mempalace_diary_read` is buried. Add a routing row: "Resume prior session continuity" → `mempalace_diary_read`.
- **Missing specialist routes.** `mempalace_kg_timeline` and `mempalace_file_context` are common enough to deserve first-class rows.
- **`mempalace_check_duplicate` is too soft.** If duplicate avoidance matters, say "call before filing substantial new prose," not "optionally."
- **Never-list incomplete.** Add: never call `mempalace_delete_wing` / `mempalace_delete_drawer` unless explicitly correcting wrong data; never treat diary entries as team-authoritative memory; never infer absence from a search miss.
- **Contradiction in the README.** `README.md:284` says "The AI learns the memory protocol automatically from `mempalace_status`. No manual configuration," while `docs/LLM_USAGE_RULES.md:3` says the assistant needs explicit rules. Proposal should call that out directly — otherwise its premise looks shaky.
- **Pushback on premise.** "One universal usage block" is right; "one universal install/injection flow" is not. `AGENT_INSTALL.md:553–650` is inherently host-specific; forcing universality there makes it worse.

### 6.1 Action items (for round-2)

1. Rewrite Routing table per bullets 1–2 and 8.
2. Split into **Core (≤ 80 lines)** + **Appendix** (query craft, drawer template, maintenance).
3. Soften "search before everything" to "search before substantial exploration when prior context could plausibly exist."
4. Strip magic numbers (`0.5`, `0.9` as user-facing) from rules; keep the 0.9 duplicate threshold as tool-internal only.
5. Replace "host's todo list" / "host's stable agent ID" with neutral terms; require `MEMPALACE_AGENT_NAME` env var for diary attribution.
6. Upgrade `mempalace_check_duplicate` wording from optional to required for substantial new prose.
7. Extend Never list with the three additions above.
8. Add a README reconciliation section: `README.md:284` claim is aspirational — downgrade it or state explicit rules are still required until MCP `tool_list` descriptions carry the full protocol.
9. Scope: keep `AGENT_INSTALL.md` §7 host-specific. Universality target is `LLM_USAGE_RULES.md` only.

---

## 7. Round-2 Status (2026-04-21)

Revised `docs/LLM_USAGE_RULES.md` in place. Codex validation pass:

| Item | Status | Note |
|------|--------|------|
| 1. Routing table fixed | FIXED | Specialist routes correct; `traverse`/`find_tunnels` scoped to palace navigation. |
| 2. Core ≤ 80 lines | PARTIAL | Core is 101 lines (down from ~149). Further trimming would drop substantive content; 80 was aspirational. |
| 3. Soften "search before everything" | FIXED | Now: "before substantial repo exploration when prior context could plausibly exist." |
| 4. Drop magic numbers | FIXED | All user-facing numeric thresholds gone. |
| 5. Neutral agent identity | FIXED | `MEMPALACE_AGENT_NAME` env var; no host-specific terms. |
| 6. `check_duplicate` required | FIXED | Mandatory for substantial new prose. |
| 7. Extended Never list | FIXED | Delete-guards, diary non-authoritativeness, absence-from-miss. |
| 8. README contradiction | FIXED | Called out explicitly near the top of the rules. |
| 9. Keep install flow host-specific | FIXED | Scope clarified; only usage rules are universal. |

Round-2 polish (new issues raised during validation, now applied):
- PII vs `people` wing ambiguity resolved — explicit carve-out for collaborator context.
- `mempalace_find_tunnels` split into its own routing row with an explanatory trigger.
- Shell example reshaped — no angle-bracket placeholders in runnable commands.

Remaining follow-up (out of scope for this round):
- Sync `AGENT_INSTALL.md` §7.3 inline block with the revised `LLM_USAGE_RULES.md`, or replace the inline block with a source-file marker to prevent drift.
- Reconcile or downgrade `README.md:284` ("AI learns protocol automatically from `mempalace_status`").
