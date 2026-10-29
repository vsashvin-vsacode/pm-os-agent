# Agent Line Map: Cortex PM Chief-of-Staff Agent

> Module 1 · The Agent Line
>
> ✅ **What this validates:** every risky action has a clear owner, by the end you'll have proven an above/below-the-line map with HITL checkpoints, scored on reversibility, blast radius, and measurability.

## The workflow, decision by decision

List every discrete decision or action in your agent's workflow, then score each one and place it **above** the line (a human owns it) or **below** (the agent owns it). Borderline calls get an HITL checkpoint.

| Decision / action | Reversibility (H/M/L) | Blast radius (H/M/L) | Measurability (H/M/L) | Above / Below | HITL? |
|---|---|---|---|---|---|
| 1. Pull project state + activity | H | L | H | Below | · |
| 2. Decide relevant context | H | M | L | Below | required: excluded-items list shown to reviewer |
| 3. Draft the update | H | L | M | Below | required: human reads every draft at #8 |
| 4. Decide tone / commitment level | H | M | L | Below | required: commitments callout (status color, dates, promises) at #8 |
| 5. Flag at-risk / escalation items | H | L | M | Below | required: flags reviewed in the draft at #8 |
| 6. Choose what to escalate | H | M | M | Below | required: triggers checklist (one line per norm) at #8 |
| 7. Propose a story batch (capped) | H | L | M | Below | required: queue approval, each story tagged to PRD or marked as Cortex's addition |
| 8. Post an update / approve a company-wide one | L | H | M | Above | required: only a human posts (Cortex has no publish tool) |

## Agent anatomy (sketch)

- **Model:** Claude Sonnet 5.5 by default. Escalate to Claude Opus 5.5 by task type (company-wide updates, or anything involving a Sev-1), which ties model spend to blast radius.
- **Tools:** read: `get_project`, `get_activity`, `search_past_updates`, `get_roadmap` (flags confidential items), `get_norms` · queue: `propose_stories` (capped at 8, creates nothing). **No publish, create, close or merge tools, by design**, so the #8 line is enforced by what Cortex can't call.
- **Memory:** persist the human-owned sources (roadmap, norms, past *approved* updates, decision log); purge each run's working context and drafts. This keeps what counts as true above the line.
- **Loop:** _placeholder, defined in M2 loop-spec.md_
- **Bounds:** max 6 iterations · 120s timeout · $0.50/run ($5/day console cap) · queue cap 8 · `STOP`-file kill switch · queued stories withdrawn on any halt. All enforced outside the model; see [M5 bounds-and-evals.md §1](../05-bounds-evals/bounds-and-evals.md).
- **Evals:** 6 trajectory cases (EV-1 to EV-6, incl. recovery and jailbreak) replayed via R1–R5 before every change; see [M5 bounds-and-evals.md §3–§5](../05-bounds-evals/bounds-and-evals.md).

## The golden rule, applied

1. **Pull project state + activity** sits below the line because it's easy to reverse (just re-run it), has a low blast radius (reading changes nothing), and is easy to verify against the source. **Deciding factor: blast radius.**
2. **Decide relevant context** sits below the line with a required HITL because it's easy to reverse (re-run with different context), has a medium blast radius (a dropped item spreads through the draft, the flags and escalation), and is hard to verify (an omission is invisible unless you already know it should be there); the excluded-items list makes gaps visible. **Deciding factor: measurability.**
3. **Draft the update** sits below the line with a required HITL because it's easy to reverse (delete or rewrite it), has a low blast radius (it's just text until someone sends it), and is only partly verifiable (facts check out, framing is judgment); every draft passes a human at #8. **Deciding factor: blast radius.**
4. **Decide tone / commitment level** sits below the line with a required HITL because it's easy to reverse while in the draft, has a medium blast radius (an implied date can become a promise to leadership), and is hard to verify (implied promises slip past a skimming reviewer); the commitments callout makes every status color, date and promise visible at #8. **Deciding factor: measurability.**
5. **Flag at-risk / escalation items** sits below the line with a required HITL because it's easy to reverse (remove a wrong flag), has a low blast radius (a flag only adds information), and is only partly verifiable (raised flags can be checked, missed flags are invisible); flags are reviewed in the draft at #8. **Deciding factor: blast radius.**
6. **Choose what to escalate** sits below the line with a required HITL because it's easy to reverse within a run, has a medium blast radius (an unescalated Sev-1 can become a "Green" update), and is moderately verifiable (the triggers are human-written rules, though judgment calls slip through); the triggers checklist makes each rule visible at #8. **Deciding factor: measurability.**
7. **Propose a story batch (capped)** sits below the line with a required HITL because it's easy to reverse (reject and nothing was created), has a low blast radius (a capped queue, nothing exists until approved), and is only partly verifiable (stories trace to the PRD, but "right stories" is judgment); traceability tags show what goes beyond the PRD. **Deciding factor: blast radius.**
8. **Post an update / approve a company-wide one** sits above the line because it's hard to reverse (once posted it can't be unread), has a high blast radius (leadership or the whole company sees it and acts on it), and is only verifiable after the damage is done; only a human posts, and Cortex has no publish tool. **Deciding factor: reversibility.**

## Hardest call

**#4, Decide tone / commitment level.** My scores overturned my own instinct; measurability settled it.

- **Step 1:** placed it below, no gate, on the grounds that it's wording inside a draft and #8 would catch implied commitments. I kept it below through a push-back.
- **Step 2:** I scored measurability L myself, because implied promises slip past a skimming reviewer. That meant #8 couldn't reliably catch what I was counting on it to catch.
- **Step 3:** moved to a required HITL with a **commitments callout**: every status color, date and promise is listed separately so the reviewer at #8 approves them explicitly.
