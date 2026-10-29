# Build Insights: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 4, what you learned building it
>
> ✅ **What this validates:** you can reflect on what building it taught you, by the end you'll have proven the friction, the learning, and the aha that changes how you'd design your next agent.

## Friction

*(default, accepted)*

- **The safety net was hard to test because the agent behaved.** In M3, Sonnet 5.5 refused to invent figures, so testing the critic meant planting a fake metric and date by hand. In M4, the first withheld-source probe ended SUCCESS with a "provisional Green," and the critic had nothing to catch, because it only checks what's in front of it.
- **Bounds that looked done weren't.** In M5, the timeout and kill switch existed in the spec but not in the code, and the iteration cap stopped the loop but left 4 stories orphaned in the approval queue.
- **Rules drifted from enforcement.** In M6, the team norms Cortex reads still said a 10-story cap after the code enforced 8, and the critic passed the wrong number because it checked against what Cortex read.

## Learning

*(default, accepted)*

1. **Check the cheap things in code before paying for judgment.** A heading check bounces a malformed draft before any critic call is spent (M2).
2. **A bound on paper isn't a bound.** If a limit isn't a counter, a clock, a budget, or a missing tool, the model can talk its way past it (M5).
3. **Stopping a run isn't containing it.** Every halt needs a cleanup path, or the side effects outlive the run (M5).

## Aha moment

"The jailbreak didn't fail because the model was smart; it failed because the tools weren't there."

## What you'd do differently

*(default, accepted)* Keep every limit in one place. The story cap lived in code, `.env`, `.env.example`, and the team norms, and they drifted apart. Next time, the norms the agent reads would be generated from the same config the code enforces, and a check would fail the build if they disagree.
