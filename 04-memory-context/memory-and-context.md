# Context Engineering & Memory: Cortex PM Chief-of-Staff Agent

> Module 4 · Context Engineering & Memory
>
> ✅ **What this validates:** the agent reasons on the right, safe inputs, by the end you'll have proven a context budget, per-source retrieve-vs-long-context decisions, and a memory map with risk mitigations.
>
> 🗂️ **How the lab maps to this file:** In **Part A** (before the lecture) you don't edit this file, you rough-draft on scratch, focused on the per-source calls in **section 2** plus a quick remember/forget + "how it rots" sketch. In **Part B** (after the lecture) you complete **all five sections**; the Lab Guide's guided builder writes this file for you to copy in and commit.

## 1. Context budget

Each loop iteration receives Cortex's instructions (`CORTEX_SYSTEM`), any critic / heading feedback from this run, and the sources below. **Priority order: rules before evidence.** Most protected first; cut from the bottom if space runs short:

1. **Task brief** (long-context): no brief, no job; injections hide here, so it's never trimmed.
2. **Team norms** (long-context, fetched fresh each run): every rule must apply; trimming a norm is a silent gap.
3. **This project's activity window** (retrieve): the cited evidence; without it there's no grounded update.
4. **Roadmap slice for this project + embargoed-names list** (retrieve): framing, and the names list keeps EXCLUDED ITEMS honest.
5. **2–3 most relevant past updates** (retrieve): tone and precedent; **first to cut**.

_Today a run uses a few tens of thousands of tokens against a 1M window, so nothing is actually cut yet. The order is for when real Jira / Slack data arrives._

## 2. Retrieve vs. long-context: per source

For each data source, decide: **retrieve** (narrow a large/changing corpus to the relevant slice) or **long-context** (just include a bounded set you can reason over).

| Source | Size / volatility | Decision | Deciding factor | Why |
|---|---|---|---|---|
| `get_activity` | large, grows weekly | **Retrieve** | **Citation** | Every claim must cite a specific PR. |
| `search_past_updates` | unbounded, grows weekly | **Retrieve** | **Size** | History is unbounded and grows weekly. |
| `get_roadmap` | medium, slow-changing; confidential flags | **Retrieve** | **Citation / audit** | Confidential details never enter context. |
| `get_norms` | medium, must stay current | **Long-context** (fresh each run) | **Citation / audit** | TRIGGERS CHECKED must cover every norm. |
| `get_task` | one short static doc | **Long-context** | **Size** | One short bounded brief. |

_Built in M4 Step 4: `get_roadmap(project_id)` now returns only this project's section plus the embargoed project **names**; Orbit/Pulsar details never enter context (verified: zero detail lines in the grounded run's trace)._

## 3. Retrieval quality plan

Moves chosen per retrieve source by its **worst failure mode**, not all five everywhere. No retrieve source is naive RAG.

| Source | Worst failure | Routing | Doc grading | Reranking | Self-verification | Caching |
|---|---|---|---|---|---|---|
| `get_activity` | **Wrong-project pull** | ✅ scope to this run's `project_id` | ✅ keep only this week's window | (not needed: one project, one week) | ✅ critic checks A + B: every ID and figure traces to pulled activity | ❌ changes weekly |
| `search_past_updates` | **Off-project precedent** | ✅ this project's updates + global decisions | ✅ drop off-project and confidential entries (Orbit / Pulsar decisions) | ✅ most recent first, keep top 2–3 | (not needed: shapes tone, not cited as fact) | (optional: past updates never change) |
| `get_roadmap` | **Confidential leak** | ✅ this project's section + embargoed *names* only | ✅ code strips any CONFIDENTIAL / EMBARGOED section before Cortex sees it | (not needed: one section) | ✅ critic check C: no confidential item in the update body (backstop) | ❌ a stale copy wouldn't know Pulsar is embargoed |

**Long-context sources** need no retrieval moves: `get_norms` is fetched fresh every run (never cached); `get_task` is the brief itself.

_Build status: **built**: `get_activity` routing (project-scoped), `get_roadmap` routing + grading (M4 Step 4), self-verification via the critic (checks A, B, C), and a stop rule: a DONE draft is STUCK if `get_project` / `get_activity` was never pulled (the withheld-source probe showed Cortex otherwise reaches #8 with a "provisional Green"). **Still design only**: `get_activity` week-window grading, `search_past_updates` routing / grading / reranking._

## 4. Memory map (your PM brain)

**Write rule (M1 agent line):** Cortex **never writes** episodic or semantic memory. Unapproved drafts shouldn't become precedent; what counts as true stays above the line.

| Memory type | What Cortex stores | Who writes it | Scope / TTL |
|---|---|---|---|
| **Working** (in-loop) | Brief, tool results, drafts, counters, critic and heading feedback | Cortex + the loop | **This run**, purged at the end |
| **Episodic** (past runs) | Past **approved** updates + decision log; the **dedupe ledger** (message IDs + project/week keys) | **Humans** (updates, decisions); the loop (ledger) | Updates/decisions **12 months**; ledger **8 weeks**; per project |
| **Semantic** (durable facts/prefs) | Team norms, roadmap facts, project metadata | **Humans only**, via the source files | **No Cortex-held copy**: re-read fresh every run; the source *is* the memory |
| **Shared** (across agents) | The run's source log + draft (Cortex and the critic); `critic-log.jsonl` | The loop | Source log + draft **this run**; critic log **90 days** (audit) |

## 5. Memory risks & mitigations

| Risk | Where it bites Cortex | Mitigation |
|---|---|---|
| **Drift** | Week-over-week framing creeps (e.g. "Green" becomes the default because Cortex reuses past tone). | Only **human-approved** updates are precedent (write rule); reranking keeps just the **2–3 most recent**; critic **check B** requires every status color to trace to this week's data. |
| **Poisoning** | A bad input trusted forever: an injection in a brief, or a false entry slipped into the decision log / past updates. | **Cortex can't write memory** (M1 line); sources change only via a **reviewed git commit** (like the 2026-07-06 data-pack ingest); briefs are data, not instructions; critic checks **C + D**, no publish tool as backstop. |
| **Staleness** | Cortex reasons on old facts; a cached roadmap wouldn't know Pulsar became embargoed this week. | **No caching** of activity, roadmap or norms; norms **re-read fresh** every run; activity graded to **this week's window**; episodic TTL 12 months. |
| **Confidential / PII / retention** | Confidential projects, or names / customer details in activity, kept longer than needed. | **Per-project scoping**; roadmap **grading strips confidential sections**; `run-output/` gitignored and purged; critic log **90-day TTL**. TTLs become **M5 bounds**. |
