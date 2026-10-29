# Production & Autonomy: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 5, how you'd ship it, govern it, and widen trust over time
>
> ✅ **What this validates:** you can ship it, govern it, and widen trust deliberately, by the end you'll have proven an autonomy dial, a Trust Ladder rung with its eval gate, and a governance plan.

## Autonomy Dial by segment

_Autonomy is a product decision per user, not one global setting._

| Segment | Desired autonomy | Why |
|---|---|---|
| **Seasoned PM on a stable project** (owns it, months of approved updates, no open Sev-1) | Supervised today → bounded-autonomous for PRD-traced stories only, once the Trust Ladder gate is met. Posting, the Green call, and Cortex's own story additions still pause. | Because they're experts, they'll get it first. But not yet, because Cortex hasn't passed the gate. |
| **New PM / new to the project** (first ~4 weeks) | Assisted: every story, flag, and status is approved by the PM | New PMs stay at assisted because they are still learning. |
| **Exec-facing / company-wide update** (audience: leadership, all-hands) | Supervised, fixed: every checkpoint, stronger model (M1), never widens | Exec-facing updates never widen because there is a lot of risk due to mistakes. |

Posting stays above the line for every segment; the dial only moves below-the-line checkpoints.

## Trust Ladder

- **Current rung:** Supervised (by design), proven on fixtures only. Because it does the work but I approve everything.
- **Next rung:** bounded-autonomous for PRD-traced stories, seasoned-PM segment only (see Autonomy Dial).
- **Eval gate to reach the next rung:** over 6 weekly runs on real project data, with at least 30 story decisions logged in shadow (Cortex records whether it *would* auto-approve; the PM decides as usual):
  - **EV-4 (task completion, "right stories"):** Cortex's would-approve call agrees with the PM's decision on ≥90% of PRD-traced stories, and **0** stories it would approve that the PM rejected. 0 because one wrong story costs a sprint.
  - **EV-5 (jailbreak):** 100% pass, with 0 context-level leaks.
  - **EV-6 (bounds):** 0 halted runs that leave stories queued.
  - **Replay set R1–R5:** 100% pass on every change during the window.
- **Incident record that counts as clean for the window:** 0 leaks · 0 invented figures reaching a human · 0 wrong-status updates · ≤1 STUCK run that needed a manual fix.
- **Incident record so far:** fixtures only, no real-data runs yet. On fixtures: 0 leaks, 0 invented figures reaching a human (the M3 tampered figure was caught by the critic), 0 posts. One drift found and fixed on 2026-10-29: the team norms said a 10-story cap while code enforced 8; the critic passed the wrong number because it checks against what Cortex read.

## Deployment plan

*(default, accepted)*

- **Runtime:** serverless function, matching the M2 loop type: the hook fires on each inbound PM brief (event trigger), and the Monday 9am cron sweep is a scheduled trigger. Cortex runs about 2 minutes a week, so an always-on server would sit idle. Not built yet; runs are started by hand today.
- **Operator / on-call owner:** the PM (operator). Backup: the eng lead. Escalated or STUCK runs go to the operator; if they're out, to the backup within 1 business day.
- **Rollback:** three levels, fastest first. (1) Drop the dial a rung for the affected segment (per-segment setting). (2) Kill switch: a shared `STOP` flag in config (the serverless version of `00-build/STOP`) halts Cortex before its next model or tool call and withdraws queued stories. (3) Revert: redeploy the last tagged version that passed replay set R1–R5.
- **Monitoring:** replay pass rate (R1–R5) · escalation and STUCK rate per week · cost per run and per day against the $0.50 and $5 caps · critic fail rate from `critic-log.jsonl` · trust incidents.

## ROI metrics (beyond adoption & tokens)

| Metric | Target | How it's captured |
|---|---|---|
| **Outcome:** PM time per weekly update (brief → approved update) | from ~60 min by hand to ≤15 min reviewing Cortex's draft *(assumed baseline, to be measured in the 4 weeks before rollout)* | PM logs review time for 4 weeks before and after; run start and approval timestamps as a cross-check |
| **Cost-to-serve:** $ per approved update (model spend + PM review time) | model cost ≤ $0.15 per run (fixture runs today: $0.07–$0.10); $5/day cap respected | run cost printed on every STOP line, plus review time from the Outcome metric |
| **Trust incidents:** incidents reaching a human or leadership (leak, invented figure, wrong status, orphaned story) | 0 per month; any incident drops the dial a rung | `critic-log.jsonl` + weekly trace review (M5 §4) + the PM flagging it in review |

## Widen-autonomy decision rule

*(default, accepted)* The dial turns up one notch for one segment and one action type only when that rung's Trust Ladder gate is met in full over its window, the operator signs off in writing, and any trust incident during the window resets the window to zero; any incident after widening drops the dial back a rung immediately.

## Governance & forward strategy

- **Compliance:** never in a prompt: embargoed project details (`get_roadmap` returns names only), customer PII, or credentials. Keys live in `.env`, never committed. Real-data runs pull only project metadata and PR/issue titles, never ticket bodies or customer records.
- **Safety:** above the line for everyone, at every rung: posting an update, committing a date, merging, closing a bug; those tools don't exist. Kill switch: a shared `STOP` flag anyone on the team can pull.
- **Reliability:** caps of 6 iterations · 120s · $0.50/run · $5/day · 8 stories. Escalate on stuck. If the model is down, the run ends STUCK after the client retries, the operator is notified, and that week's update is written by hand; no retries pile up.
- **Strategy:** next, widen new PMs from assisted to supervised after their first 4 weeks, gated by EV-4 first-pass approval ≥80% over that PM's first 4 runs, with 0 incidents.
