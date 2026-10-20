# Loop Spec: Cortex PM Chief-of-Staff Agent

> Module 2 · Loop Engineering, ★ Deliverable 2
>
> ✅ **What this validates:** the agent knows when to run and when to stop, by the end you'll have proven a one-page Loop Spec with a trigger, a definition of "done," and explicit stop conditions.
>
> Your one-page blueprint for how the work you handed to the agent (M1) actually *runs*.
> An agent is just a prompt that fires itself, this spec says when it fires, what "done" means, and what it needs to do the job. Living document; refine as the course progresses.

## 1. Trigger & loop type

**Chosen type:** hook (primary) + cron (backup)

- **Hook:** fires on each inbound PM task brief (e.g. "put together this week's update for P-NORTH").
- **Cron:** a Monday 9am sweep that assembles the weekly update for each project if no brief has already produced one.

**Why:** the work is request-driven but weekly.

**Ruled out:**
- **Cron only:** can't respond to ad-hoc requests like "propose stories"; it would wait until Monday.
- **Heartbeat:** checking every few minutes burns cost polling for work that arrives a few times a week.
- **Goal:** "iterate until the critic passes" is how a run works, not what starts one; it's already inside each run.

**Idempotency / dedupe:** the hook skips any brief whose message ID it has already processed. Before drafting a weekly update, Cortex checks for an existing draft keyed on **project + ISO week**; if one exists, the cron sweep skips that project. Covers both risks: duplicate deliveries and hook-then-cron overlap.

## 2. Goal / definition of done

A status update grounded in the pulled activity, **plus the four review aids the #8 reviewer relies on** (from agent-line-map.md):

- **EXCLUDED ITEMS:** what Cortex filtered out (#2)
- **COMMITMENTS:** every status color, date and promise, listed separately (#4)
- **TRIGGERS CHECKED:** one line per escalation norm and whether it fired (#6)
- **Story traceability:** each proposed story tagged to its PRD item or marked as Cortex's addition (#7)

Draft saved for review, stories queued for approval; **Cortex never sends.** A draft without the four aids isn't done: it hands the reviewer an incomplete package. It's also detectable: each section is checked for presence.

**Validation:** not Cortex grading itself. Code checks the sections are present, then an independent critic (a separate model call that never saw the drafting context) judges the content.

## 3. Stop conditions

| Condition | What it looks like | What happens |
|---|---|---|
| **Success** | Code finds all four required section headings in the draft, **then** the critic returns `pass`. A missing heading sends the draft straight back to Cortex without spending a critic call. | Stop. Save the draft to `run-output/`, hold it at the HITL checkpoint (#8). Nothing posted. |
| **Stuck / give up** | Any of: **8 iterations** reached · **2 revisions** used (critic rejections **and** heading-check bounces count together) · **$0.50 cost cap** hit · **required data missing**: `get_project` / `get_activity` returns not-found (stop immediately) or a transient error (at most 3 retries). | Stop. Log why, save the last draft as HELD, hand it to a human. Missing data shouldn't depend on the model noticing. |
| **Escalate to human** | **Detected in code:** a Sev-1 in `get_activity`, a `batch_exceeds_queue_cap` rejection from `propose_stories`, a model refusal. **Declared by the model:** prompt-injection attempts and unconfirmed-date requests; Cortex ends with `ESCALATE:` and the TRIGGERS CHECKED list shows which rule fired. | Stop. Save the draft as HELD with the reason, hand it to a human: the #6 HITL checkpoint (triggers checklist). Never posted. |

## 4. State

**Two layers, scoped per project.** Dedupe needs to persist.

- **Across runs (persisted):** the dedupe ledger (processed message IDs + project/ISO-week keys) and the human-owned sources (roadmap, norms, past *approved* updates, decision log).
- **Within a run (purged at the end):** iteration / revision / cost counters, the source log the critic checks against, and the last draft.
- **Scope:** each run sees only its own project's data, so no confidential leakage between projects.

## 5. The five things a loop can lean on

| Component | For Cortex |
|---|---|
| **Work tree** (isolated workspace per run, a git worktree) | Not needed yet, because Cortex writes only one draft file per run to `run-output/` and never touches the repo. Revisit when runs happen in parallel or edit files. |
| **Skills** (reusable capabilities) | Not needed yet, because there's one workflow and its playbook lives in `prompts.py` + `get_norms`. A "weekly update format" skill makes sense once there are several task types. |
| **Plugins / connectors** (tools & access, optional if you don't have one yet) | Plan, not wired: fixtures today; later Jira/GitHub for activity and Slack/email as the inbound source for the hook. |
| **Subagents** (independent check when the loop can't grade itself) | The **critic** already plays this role: a separate model call that never sees the drafting context. Full design → M3 `orchestration-map.md`. |
| **State tracking** | The two layers in §4: dedupe ledger across runs; counters + source log within a run. |

> Context plan (M4) and the hand-off to bounds & evals (M5) come in later modules, you'll add them to their own deliverables then, not here.

## Link to live loop

- Loop, stop conditions and code-detected triggers: [`00-build/agent.py`](../00-build/agent.py) (`REQUIRED_SECTIONS`, `REQUIRED_DATA_TOOLS`, `code_escalation_triggers`, `run`)
- Definition of done + critic checks: [`00-build/prompts.py`](../00-build/prompts.py) (`CORTEX_SYSTEM`, `CRITIC_SYSTEM` check 7)
- **Design only, not yet built:** the hook + cron triggers and the dedupe ledger (§1, §4). Runs are started by hand today: `python agent.py [happy|missing-data|jailbreak]`.
