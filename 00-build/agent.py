"""Cortex, a minimal, explicit agent loop you (and your coding agent) can read end
to end. This is the agent you ship: your PM chief-of-staff. You build it by
directing your coding agent (Claude Code / Cursor / Codex) to shape this file. You
never have to hand-write it.

Every bound the course talks about is visible right here in code, not buried in a
framework: the max-iteration counter, the cost cap, the revision cap, the
stop/escalate conditions, the auto-queue cap, and the absence of any publish tool.

Usage (ask your coding agent to run these for you, or run them yourself):
    python agent.py                # runs the happy-path task (weekly status update)
    python agent.py missing-data   # the stuck/escalate case
    python agent.py jailbreak       # the prompt-injection refusal case

Every run ends by showing the drafted status update in a FINAL STATUS UPDATE block
(or LAST DRAFT, held, if a bound trips), and saves it to run-output/. That file is
always a draft held for a human, it is never posted, there is no publish tool.

Requires ANTHROPIC_API_KEY in your environment (see .env.example). Model and bounds
are read from env so you can tune them, that tuning is your M5 deliverable.

The loop is deliberately transparent (hand-written tool-calling on the anthropic
client) so a grader can see the machinery. Keep the bounds explicit if you rework it.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic

import tools
from critic import review
from prompts import CORTEX_SYSTEM

try:  # load .env if python-dotenv is installed; harmless if it isn't
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# --- Bounds (your M5 deliverable: tune these and justify them) ----------------
MODEL = os.environ.get("CORTEX_MODEL", "claude-sonnet-5-5")
MAX_TOKENS = 16000  # per-response output ceiling (the API requires one)
MAX_ITERATIONS = int(os.environ.get("CORTEX_MAX_ITERATIONS", "8"))
MAX_REVISIONS = int(os.environ.get("CORTEX_MAX_REVISIONS", "2"))
COST_CAP_USD = float(os.environ.get("CORTEX_COST_CAP_USD", "0.50"))
MAX_QUEUE_ITEMS = int(os.environ.get("CORTEX_MAX_QUEUE_ITEMS", "10"))
# Rough $ per 1M tokens for your chosen model, set to match its pricing.
PRICE_IN = float(os.environ.get("CORTEX_PRICE_IN_PER_M", "2.00"))
PRICE_OUT = float(os.environ.get("CORTEX_PRICE_OUT_PER_M", "10.00"))

TOOL_SCHEMAS = [
    {"name": "get_project", "description": "Look up a project by its ID (status, flags, linked PRD).",
     "input_schema": {"type": "object", "properties": {
         "project_id": {"type": "string"}}, "required": ["project_id"]}},
    {"name": "get_activity",
     "description": "Pull recent engineering activity for a project (merged PRs, open issues, Sev-1s).",
     "input_schema": {"type": "object", "properties": {
         "project_id": {"type": "string"}}, "required": ["project_id"]}},
    {"name": "search_past_updates",
     "description": "Search previous status updates and decisions for tone and precedent.",
     "input_schema": {"type": "object", "properties": {
         "query": {"type": "string"}}, "required": []}},
    {"name": "get_roadmap",
     "description": "Return this project's roadmap section plus the NAMES of embargoed "
                    "projects (their details are withheld). Pass the run's project_id.",
     "input_schema": {"type": "object", "properties": {
         "project_id": {"type": "string"},
         "query": {"type": "string"}}, "required": ["project_id"]}},
    {"name": "get_norms", "description": "Return the team norms / PM playbook the agent must follow.",
     "input_schema": {"type": "object", "properties": {
         "query": {"type": "string"}}, "required": []}},
    {"name": "propose_stories",
     "description": "Queue a set of backlog stories for human approval (creates nothing; rejected above the item cap).",
     "input_schema": {"type": "object", "properties": {
         "project_id": {"type": "string"},
         "stories": {"type": "array", "items": {"type": "string"}},
         "reason": {"type": "string"}}, "required": ["project_id", "stories"]}},
]


class Bounds:
    """Tracks spend and trips the cost cap. This is enforced OUTSIDE the model."""

    def __init__(self):
        self.cost = 0.0

    def add(self, usage) -> None:
        self.cost += (usage.input_tokens * PRICE_IN
                      + usage.output_tokens * PRICE_OUT) / 1_000_000

    def over_cap(self) -> bool:
        return self.cost >= COST_CAP_USD


OUTPUT_DIR = Path(__file__).parent / "run-output"

# --- Definition of done + stop conditions (M2 loop-spec.md §2-§3) -------------
# A DONE draft must carry the four review aids the #8 reviewer relies on. Code
# checks they are present BEFORE spending a critic call.
REQUIRED_SECTIONS = ("EXCLUDED ITEMS:", "COMMITMENTS:", "TRIGGERS CHECKED:",
                     "STORY TRACEABILITY:")
# Required data: a not-found here means stop now (stuck), never invent it.
REQUIRED_DATA_TOOLS = ("get_project", "get_activity")
MAX_TOOL_RETRIES = 3  # transient tool errors only; not-found is never retried

# Validator fail-action + caps (M3 orchestration-map.md §5). Separate budgets so
# format slips don't starve content fixes: 1 format retry (heading check) and
# MAX_REVISIONS critic revisions. C/D failures cross the M1 line: escalate now.
MAX_FORMAT_RETRIES = 1
ESCALATE_CHECKS = {"C", "D"}
CRITIC_LOG = OUTPUT_DIR / "critic-log.jsonl"  # every verdict, always logged

# The three exits, plus what each means for the human.
OUTCOMES = {
    "SUCCESS": "FINAL STATUS UPDATE (SUCCESS: sections present + critic passed, NOT posted)",
    "STUCK": "LAST DRAFT (STUCK: halted and logged, NOT posted, handed to a human)",
    "ESCALATED": "LAST DRAFT (ESCALATED: held for a human decision, NOT posted)",
}


def banner(text: str) -> None:
    print(f"\n{'=' * 64}\n{text}\n{'=' * 64}")


def emit_deliverable(which: str, draft: str, *, outcome: str,
                     reason: str, cost: float) -> None:
    """Surface AND persist Cortex's drafted status update so it can't get lost in
    the scroll-back. This is still a DRAFT held for human review, never a post,
    there is no publish tool, and a stuck or escalated run is held on purpose.

    Runs on every exit: SUCCESS prints the final update; STUCK or ESCALATED
    prints the LAST draft it managed to write plus why it was held.
    """
    banner(OUTCOMES[outcome])
    if draft.strip():
        print(draft.rstrip())
    else:
        print("(Cortex stopped before it produced a draft, nothing to show.)")
    print(f"\nOutcome: {outcome}. Reason: {reason}")

    if draft.strip():
        OUTPUT_DIR.mkdir(exist_ok=True)
        out = OUTPUT_DIR / f"status-update-{which}.md"
        out.write_text(
            f"<!-- Cortex draft, {outcome}; NOT posted. Run cost ~ ${cost:.4f}. -->\n"
            f"<!-- {reason} -->\n\n{draft.rstrip()}\n", encoding="utf-8")
        print(f"\nSaved draft -> {out.relative_to(Path(__file__).parent)}  "
              f"(for your review, nothing was posted)")


def log_verdict(which: str, step: int, verdict: dict) -> None:
    """Append one critic verdict to the run log (the 'log always' fail-action)."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "fixture": which, "step": step, "verdict": verdict.get("verdict"),
             "failed_checks": verdict.get("failed_checks", []),
             "reasons": verdict.get("reasons", [])}
    with CRITIC_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def call_tool(fn: str, args: dict) -> dict:
    """Run one tool, retrying only transient failures (exceptions)."""
    last_error = None
    for attempt in range(1, MAX_TOOL_RETRIES + 1):
        try:
            return tools.TOOLS[fn](**args)
        except Exception as e:  # a tool crash is transient; not-found is a result
            last_error = e
            print(f"          !! {fn} failed (attempt {attempt}/{MAX_TOOL_RETRIES}): {e}")
    return {"error": "tool_failed", "detail": str(last_error), "attempts": MAX_TOOL_RETRIES}


def code_escalation_triggers(fn: str, result: dict) -> list[str]:
    """Escalation triggers detected in code, so they don't depend on the model
    noticing. Structured signals only; judgment calls stay with the model."""
    triggers = []
    if fn == "get_activity":
        for item in result.get("activity", []):
            if str(item.get("severity", "")).lower() == "sev-1":
                triggers.append(f"Sev-1 open: {item.get('id')} {item.get('title')}")
    if fn == "propose_stories" and result.get("error") == "batch_exceeds_queue_cap":
        triggers.append(f"story batch over cap ({result.get('count')} > {result.get('cap_items')})")
    return triggers


def run(which: str = "happy") -> None:
    client = anthropic.Anthropic()
    bounds = Bounds()
    task = tools.get_task(which)
    if "error" in task:
        print(task)
        return

    banner(f"CORTEX RUN, fixture: task-{which}  (auto-queue cap {MAX_QUEUE_ITEMS} items)")
    print(task["body"])

    messages = [
        {"role": "user", "content": f"PM task brief:\n\n{task['body']}"},
    ]
    source_log: list[str] = [task["body"]]
    format_retries = 0  # heading-check bounces (budget: MAX_FORMAT_RETRIES)
    revisions = 0       # critic rejections on A/B/E (budget: MAX_REVISIONS)
    last_draft = ""
    escalations: list[str] = []  # triggers detected in code (loop-spec §3)
    called_tools: set[str] = set()  # which sources were actually pulled this run

    def stop(outcome: str, reason: str, draft: str) -> None:
        banner(f"STOP: {outcome}, {reason}. Run cost ≈ ${bounds.cost:.4f}")
        emit_deliverable(which, draft, outcome=outcome, reason=reason, cost=bounds.cost)

    for step in range(1, MAX_ITERATIONS + 1):
        if bounds.over_cap():
            return stop("STUCK", f"cost cap ${COST_CAP_USD} hit at ${bounds.cost:.4f}",
                        last_draft)

        resp = client.messages.create(
            model=MODEL, max_tokens=MAX_TOKENS, system=CORTEX_SYSTEM,
            messages=messages, tools=TOOL_SCHEMAS)
        bounds.add(resp.usage)

        if resp.stop_reason == "refusal":
            return stop("ESCALATED", "model declined the request (stop_reason: refusal)",
                        last_draft)

        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            results = []
            for call in (b for b in resp.content if b.type == "tool_use"):
                fn = call.name
                args = call.input or {}
                result = call_tool(fn, args)
                called_tools.add(fn)
                source_log.append(f"{fn}({args}) -> {json.dumps(result)}")
                print(f"\n[step {step}] TOOL {fn}({args})")
                print(f"          -> {json.dumps(result)[:300]}")

                # Stuck: required data missing. Stop now, never invent it.
                if fn in REQUIRED_DATA_TOOLS and result.get("error") in (
                        "project_not_found", "tool_failed"):
                    return stop("STUCK", f"required data missing: {fn}({args}) -> "
                                f"{result.get('error')}", last_draft)

                # Escalate: structured triggers are caught in code, not by the model.
                for trigger in code_escalation_triggers(fn, result):
                    print(f"          !! escalation trigger (code): {trigger}")
                    escalations.append(trigger)

                results.append({"type": "tool_result", "tool_use_id": call.id,
                                "content": json.dumps(result)})
            # All tool results go back together in a single user turn.
            messages.append({"role": "user", "content": results})
            continue

        # No tool calls => Cortex produced a proposed output.
        proposed = "".join(b.text for b in resp.content if b.type == "text")
        last_draft = proposed
        print(f"\n[step {step}] PROPOSED OUTPUT:\n{proposed}")

        # Escalate (code): a trigger fired during the run, so this can't be a
        # success whatever the model wrote. The human gets the draft + the reason.
        if escalations:
            return stop("ESCALATED", "detected in code: " + "; ".join(escalations), proposed)

        model_escalated = "ESCALATE:" in proposed and "DONE:" not in proposed

        # Stuck: a DONE draft built without a required source never reaches #8,
        # even if the model flags the gap itself ("provisional Green"). M4 probe.
        never_pulled = [t for t in REQUIRED_DATA_TOOLS if t not in called_tools]
        if not model_escalated and never_pulled:
            return stop("STUCK", f"required data never pulled: {never_pulled}; a DONE "
                        "draft without it can't be grounded", proposed)

        # Definition of done: a DONE draft needs all four review aids. Checked in
        # code BEFORE spending a critic call; an ESCALATE goes to a human as is.
        if not model_escalated:
            missing = [s for s in REQUIRED_SECTIONS if s not in proposed]
            if missing:
                if format_retries >= MAX_FORMAT_RETRIES:
                    return stop("STUCK", f"format retry budget ({MAX_FORMAT_RETRIES}) used; "
                                f"draft still missing {missing}", proposed)
                format_retries += 1
                print(f"\n-> heading check failed, missing {missing}; format retry "
                      f"{format_retries}/{MAX_FORMAT_RETRIES} (no critic call spent)")
                messages.append({"role": "assistant", "content": resp.content})
                messages.append({"role": "user", "content":
                                 f"Your DONE output is missing required sections: {missing}. "
                                 "Add them (exact headings) or escalate."})
                continue

        banner("CRITIC, independent validation")
        verdict = review(client, MODEL, proposed, "\n".join(source_log))
        # Estimate critic spend too.
        bounds.cost += (verdict["_usage"]["prompt"] * PRICE_IN
                        + verdict["_usage"]["completion"] * PRICE_OUT) / 1_000_000
        print(json.dumps({k: v for k, v in verdict.items() if k != "_usage"}, indent=2))
        log_verdict(which, step, verdict)

        if verdict["verdict"] == "pass":
            if model_escalated:
                return stop("ESCALATED", "Cortex declared ESCALATE (see TRIGGERS CHECKED / "
                            "its reason); critic confirmed nothing posted or leaked", proposed)
            banner("HITL CHECKPOINT, status update + any proposed stories queued for "
                   "your review. Nothing posted, no commitments made.")
            return stop("SUCCESS", "all four sections present + critic passed", proposed)

        # Tiered fail-action: C/D cross the M1 line, so no second try at looking clean.
        line_crossed = sorted(ESCALATE_CHECKS & set(verdict.get("failed_checks", [])))
        if line_crossed:
            return stop("ESCALATED", f"critic failed check(s) {line_crossed} (crosses the "
                        "M1 line), no revision", proposed)

        if revisions >= MAX_REVISIONS:
            return stop("STUCK", f"critic revision cap ({MAX_REVISIONS}) hit; still failing "
                        f"{verdict.get('failed_checks', [])}", last_draft)

        revisions += 1
        print(f"\n-> critic rejected {verdict.get('failed_checks', [])}; "
              f"revision {revisions}/{MAX_REVISIONS}, back to Cortex with the reasons")
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content":
                         "A validator rejected that for these reasons: "
                         f"{verdict['reasons']}. Fix it or escalate."})

    stop("STUCK", f"max iterations ({MAX_ITERATIONS}) reached", last_draft)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "happy")
