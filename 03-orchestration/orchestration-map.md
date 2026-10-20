# Orchestration Map: Cortex PM Chief-of-Staff Agent

> Module 3 · Orchestration & Subagents, ★ Deliverable 3
>
> ✅ **What this validates:** nothing advances unchecked, by the end you'll have proven a justified topology, a roster, and a validator with a defined fail action.
>
> Builds on your M2 Loop Spec. Only split one agent into a team when there's a real reason, coordination has a cost.

## 1. Why split? (or why not)

**Decision: minimal split, Cortex + one validator subagent (the critic).** The critic is the only reason that holds.

Current design: a hook-triggered agent (Monday cron as backup) that pulls one project's data, drafts the weekly update with four review aids and proposes capped stories, checked by an independent critic, then held at a human checkpoint.

| Reason | Applies? | Why / why not |
|---|---|---|
| Separation of concerns | No | One workflow; nothing contaminates anything else. |
| Parallelism | No | Each run is one project; copies run in parallel. |
| Independent validator | **Yes** | Cortex can't grade its own draft. |
| Context-window pressure | No | Context is small against a 1M window. |

## 2. Topology

**Pattern:** single + subagents (Cortex + one critic)

```
[Inbound PM brief (hook) / Monday 9am sweep (cron)]
        │  dedupe: message ID + project/ISO-week
        ▼
[Cortex: pulls data → drafts update + 4 review aids → queues stories (≤10)]
        │
        ├─ code: required data missing ──────────────► STUCK → human
        ├─ code: Sev-1 / over-cap / refusal ─────────► ESCALATED → human
        ▼
[Heading check (code)] ── missing section ──► back to Cortex (max 1 format retry) ─► STUCK
        │ all 4 present
        ▼
[Critic subagent (independent call)]
        ├─ fail A/B/E ──► back to Cortex with reasons (max 2 revisions) ─► STUCK → human
        ├─ fail C/D ────► ESCALATED → human (no revision)
        ▼ pass
[PM review checkpoint (#8)] ──► human posts (Cortex can't)
```

## 3. Roster

| Agent / subagent | Responsibility | Runs which Loop Spec |
|---|---|---|
| **Cortex** (chief-of-staff) | Pulls one project's data, drafts the update + 4 review aids, queues capped stories, ends with DONE or ESCALATE. | The **M2 loop**: hook + cron trigger, per project, ≤8 iterations, stop conditions in `loop-spec.md` §3. |
| **Critic** (validator subagent) | Checks each draft against rules A–E; returns pass/fail + reasons. Never edits or sends. | **No loop of its own**: one independent call per draft that passes the heading check (≤3 per run). |

_The heading check and code-detected triggers are code, not agents._

## 4. Communication & hand-offs

| From → to | What passes | Form |
|---|---|---|
| Trigger → Cortex | The PM task brief | Text, first user message |
| Cortex → Critic | The proposed draft + the **source log** (brief + every tool call and its full result) | Two text blocks in a fresh call: no conversation history, no Cortex reasoning |
| Critic → loop | Verdict + reasons | Strict JSON `{"verdict": "pass"\|"fail", "reasons": [...]}`, schema-enforced |
| Loop → Cortex (on fail) | The critic's reasons, or the missing headings | One user message: "A validator rejected that for these reasons…" |
| Loop → human | Final or held draft + outcome + reason | `run-output/status-update-<fixture>.md`, header shows SUCCESS / STUCK / ESCALATED |

**Protocol:** plain **in-process** hand-off (Python calls inside `agent.py`). **No MCP / A2A**; only needed if the critic ran as a separate service.

## 5. The validator

- **What the critic checks:** (an independent model call; it sees only the source data + the draft, never Cortex's reasoning)
  - **A. Correct project + real IDs:** every PR/issue number and the project ID appear in the pulled data.
  - **B. No invented figures or dates:** every number, metric and date traces to pulled data; no unconfirmed ship/GA date is committed.
  - **C. No confidential leak:** no CONFIDENTIAL/embargoed roadmap item in the update body (the reviewer-facing EXCLUDED ITEMS section may name it).
  - **D. Nothing acted on, cap respected:** nothing posted/created/merged; stories only queued, and within the cap or escalated.
  - **E. Review aids are true:** the four sections (EXCLUDED ITEMS · COMMITMENTS · TRIGGERS CHECKED · STORY TRACEABILITY) are substantive and match the data.
  - Each ties to an M1/M2 decision.
- **Fail action (tiered):** **revise** on A, B, E (content errors Cortex can fix with the reason in hand) · **escalate immediately, no revision** on C, D (they cross the M1 line) · **log** every rejection's verdict + reasons.
- **Revision cap:** **1 format retry** (heading check) + **2 critic revisions**, separate budgets, so format slips don't starve content fixes. Cap hit → **STUCK**: stop, hold the last draft, hand it to a human. Worst case per item: 4 drafts, 3 critic calls.
- **Pass action:** advances to the **PM review checkpoint (#8)** and is held there. Never auto-sent; posting stays above the agent line (M1).

## 6. State: shared vs isolated

**Shared inputs, isolated reasoning, fresh critic each draft.** Memory of past verdicts would anchor the critic.

- **Shared:** the source data (brief + every tool result) and the draft under review; the critic's **reasons** go back to Cortex so it can fix the problem.
- **Isolated from the critic:** Cortex's conversation, its reasoning and its earlier drafts.
- **Isolated from Cortex:** the critic's own reasoning beyond the returned reasons.
- **No memory between drafts:** each review is a fresh call; revision 2 is judged on its own merits.
- **Across runs:** both agents follow the per-project scoping from `loop-spec.md` §4; no cross-project leakage.

## 7. Cost & latency budget

**Expected + worst case, grounded in real runs (2026-10-20, Claude Sonnet 5.5).**

- **Expected:** the validator adds **1 critic call per item** (~$0.02–0.03, ~15–30 s). A clean run costs $0.05–0.07 end to end.
- **Worst case at the caps:** 1 format retry + 2 critic revisions = **4 drafts, 3 critic calls**, ~$0.30 and ~2 min before a draft reaches the PM. Observed: one revise cycle (redraft + critic) took ~30 s; a run with a format bounce + a critic rejection cost $0.16.
- **Hard ceiling:** the **$0.50 per-run cost cap** (`CORTEX_COST_CAP_USD`) stops any run regardless → M5 `bounds-and-evals.md`.
- _Estimates are from run totals; the code doesn't break cost down per call._
