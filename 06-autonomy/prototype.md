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
| 3 | **(a)** ![M4 grounded run](screenshots/m4-grounded.png) **(b)** ![M4 withheld-source run ends STUCK](screenshots/m4-withheld-stuck.png) | a grounded update citing pulled activity + a caught hallucination. **(a) Grounded:** on the ingested 2026-07-06 data pack, every claim traces to a pulled source (#820, #823, #825 and 43% vs 41% from `get_activity`; Green from `get_project`); `get_roadmap` now returns only Northstar's section + embargoed *names*, so zero Orbit/Pulsar details enter context → **SUCCESS**, ~$0.10. **(b) Withheld source:** `get_activity` temporarily removed. Cortex invents nothing ("I won't invent them") and the new stop rule halts it → **STUCK: required data never pulled**, ~$0.06. Honest note: the first probe (before the rule) ended **SUCCESS** with a "provisional Green" and nothing for the critic to catch, which is why the rule was added. | M4 |
| 4 | _[img]_ | jailbreak refused + escalated | M5 |
| 5 | _[img]_ | an iteration/cost/queue bound halting a runaway | M5 |
| 6 | _[img]_ | end-to-end run | M6 |

## How to run it

_Minimal steps for someone to reproduce the demo (env vars, and the command or the coding-agent prompt you used)._
