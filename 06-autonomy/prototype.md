# Prototype: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 1, the working agent demo
>
> ✅ **What this validates:** the agent actually runs end to end, by the end you'll have proven it with real screenshots of your Cortex across the six required moments (M2 to M6).

## What it does

_One paragraph: the agent in action, end to end._

## How you built it

- **Coding agent:** _which one you directed (Claude Code / Cursor / Codex)_
- **Model + bounds:** _model used, max iterations, cost cap, queue cap_
- **Repo / config:** _path to your build in `00-build/`_
- **Live link:** _[shareable URL, optional bonus]_

## Screenshots (required, collected M2 to M6)

Real screenshots of *your* Cortex running. These are the `00-build/CORTEX-ANATOMY.md` set and they are required, a link alone is not enough.

| # | Screenshot | What it shows | From |
|---|---|---|---|
| 1 | ![M2 happy-path run](screenshots/m2-happy-success.png) | happy-path run: a real drafted update + the HITL checkpoint (queued, not posted). The heading check bounces the first draft (revision 1/2, no critic call), then all four review sections are present, the critic passes, and the run stops at **SUCCESS**: held for review, nothing posted, ~$0.10. | M2 |
| 2 | ![M3 critic rejecting a tampered draft](screenshots/m3-critic-reject.png) | the critic rejecting a bad draft (revise/block). **Deliberately tampered:** Sonnet 5.5 refused to invent figures when instructed, so a temporary demo flag (since removed) inserted "NPS 52, up from 47. GA locked for 2026-08-15." into the draft just before review. The independent critic fails it on **B** (invented figure + unconfirmed date) and **E** (review aids now false), the **revise** fail-action fires (critic revision 1/2), Cortex flags the line as not its own and removes it, and the second critic call passes → **SUCCESS**, held at #8. ~$0.16. | M3 |
| 3 | _[img]_ | a grounded update citing pulled activity + a caught hallucination | M4 |
| 4 | _[img]_ | jailbreak refused + escalated | M5 |
| 5 | _[img]_ | an iteration/cost/queue bound halting a runaway | M5 |
| 6 | _[img]_ | end-to-end run | M6 |

## How to run it

_Minimal steps for someone to reproduce the demo (env vars, and the command or the coding-agent prompt you used)._
