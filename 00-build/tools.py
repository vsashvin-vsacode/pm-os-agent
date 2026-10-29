"""Cortex mock tools, the tools your PM chief-of-staff agent is allowed to call.

These are plain Python functions over the files in `fixtures/`. They are imported
directly by `agent.py`, so this file is the single place that defines what Cortex
can and cannot do. Ask your coding agent to add, remove, or tighten a tool here.

Design note that matters for the course: there is deliberately NO publish tool.
Cortex can read and DRAFT a status update, and it can PROPOSE backlog stories (which
are capped and queued for a human), but it can never post to a channel, create or
merge a ticket/PR, commit a ship date, or mark a launch gate. The agent line is
enforced here, in infrastructure, not by a prompt.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

# Commitment bound (M5). A run that tries to queue more than this many backlog
# stories is rejected by infrastructure and must be escalated, even if the PRD
# would justify more. Auto-committing a flood of "real" work is the money analog.
MAX_QUEUE_ITEMS = int(os.environ.get("CORTEX_MAX_QUEUE_ITEMS", "8"))


def _load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def get_task(which: str = "happy") -> dict:
    """Read the inbound PM task brief to work on.

    Args:
        which: one of "happy", "missing-data", "jailbreak".
    Returns the raw task text plus its source label.
    """
    path = FIXTURES / f"task-{which}.md"
    if not path.exists():
        return {"error": f"no task fixture named '{which}'",
                "available": ["happy", "missing-data", "jailbreak"]}
    return {"which": which, "body": path.read_text()}


def get_project(project_id: str) -> dict:
    """Look up a single project by its ID. Returns {"error": ...} if not found."""
    project_id = str(project_id).strip()
    projects = _load_json("projects.json")
    record = projects.get(project_id)
    if record is None:
        return {"error": "project_not_found", "project_id": project_id,
                "hint": "no such project in the system",
                "known_projects": list(projects.keys())}
    # Return the project WITHOUT its activity blob; activity is a separate tool call
    # so the agent has to deliberately pull it (a teachable retrieval step).
    return {k: v for k, v in record.items() if k != "activity"}


def get_activity(project_id: str) -> dict:
    """Pull recent engineering activity (merged PRs, open issues, Sev-1s) for a project."""
    project_id = str(project_id).strip()
    projects = _load_json("projects.json")
    record = projects.get(project_id)
    if record is None:
        return {"error": "project_not_found", "project_id": project_id}
    return {"project_id": project_id, "activity": record.get("activity", [])}


def search_past_updates(query: str = "") -> dict:
    """Search previous status updates and decisions for tone and precedent (the
    memory/retrieval surface).

    Naive keyword overlap over a small fixture so M4's retrieve-vs-reason lesson is
    concrete: relevant precedent is returned, irrelevant precedent is not."""
    query = (query or "").lower()
    corpus = _load_json("past-updates.json") + _load_json("decision-log.json")
    terms = {t for t in query.replace("#", " ").split() if len(t) > 2}
    hits = []
    for u in corpus:
        haystack = f"{u.get('project','')} {u.get('summary','')} {u.get('theme','')}".lower()
        if terms and any(term in haystack for term in terms):
            hits.append(u)
    return {"query": query, "matches": hits or corpus[:2],
            "note": "prior updates + decisions for precedent, team norms still govern."}


CONFIDENTIAL_MARKERS = ("CONFIDENTIAL", "EMBARGOED")


def _roadmap_sections() -> list[tuple[str, str]]:
    """Split roadmap.md into (heading, body) pairs, one per `## ` section."""
    sections, heading, body = [], None, []
    for line in (FIXTURES / "roadmap.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if heading:
                sections.append((heading, "\n".join(body).strip()))
            heading, body = line[3:].strip(), []
        elif heading:
            body.append(line)
    if heading:
        sections.append((heading, "\n".join(body).strip()))
    return sections


def get_roadmap(project_id: str = "", query: str = "") -> dict:
    """Return the roadmap slice for ONE project (M4: retrieve, not long-context).

    Routing: only the section for this run's project is returned.
    Grading: any section marked CONFIDENTIAL / EMBARGOED is stripped in code before
    the agent sees it; only the embargoed project NAMES come back, so the agent can
    say what it left out without the details ever entering its context."""
    sections = _roadmap_sections()
    embargoed = [h.split(" (")[0] for h, _ in sections
                 if any(m in h.upper() for m in CONFIDENTIAL_MARKERS)]
    base = {"project_id": project_id, "query": query, "embargoed_names": embargoed,
            "warning": "embargoed projects must never appear in any update; "
                       "their details are withheld from this tool."}

    record = _load_json("projects.json").get(str(project_id).strip())
    if record is None:
        return {**base, "error": "project_not_found", "section": None}

    short_name = record["name"].split(" (")[0].lower()
    for heading, body in sections:
        if heading.lower().startswith(short_name):
            if any(m in heading.upper() for m in CONFIDENTIAL_MARKERS):
                return {**base, "section": None,
                        "note": "this project is itself embargoed; core-team only."}
            return {**base, "section": f"## {heading}\n{body}"}
    return {**base, "section": None, "note": "no roadmap section for this project."}


def get_norms(query: str = "") -> dict:
    """Return the team norms / PM playbook. `query` is a hint; the full playbook is
    small enough to return whole so the agent can cite the exact rule it relied on."""
    text = (FIXTURES / "team-norms.md").read_text()
    return {"query": query, "norms": text}


def propose_stories(project_id: str, stories=None, reason: str = "") -> dict:
    """PROPOSE a set of backlog stories for a human to approve. This creates NOTHING
    in the tracker, it queues a request. A batch larger than CORTEX_MAX_QUEUE_ITEMS
    is rejected by infrastructure and must be escalated. This is the commitment bound,
    enforced outside the model (M5)."""
    if isinstance(stories, str):
        stories = [stories]
    if not isinstance(stories, list):
        return {"error": "invalid_stories", "stories": stories}
    if len(stories) > MAX_QUEUE_ITEMS:
        return {"status": "rejected",
                "error": "batch_exceeds_queue_cap",
                "count": len(stories),
                "cap_items": MAX_QUEUE_ITEMS,
                "action": "escalate to a human, do not split the batch to dodge the cap"}
    return {"status": "queued_for_approval",
            "project_id": str(project_id).strip(),
            "count": len(stories),
            "stories": stories,
            "reason": reason,
            "note": "queued for a human to approve, nothing was created in the tracker."}


# Registry the agent loop reads. Add a tool here and the agent can call it.
# Note what is ABSENT: there is no post_update, no create_issue, no merge_pr,
# no commit_ship_date, no close_bug, no tool that acts on the world.
TOOLS = {
    "get_task": get_task,
    "get_project": get_project,
    "get_activity": get_activity,
    "search_past_updates": search_past_updates,
    "get_roadmap": get_roadmap,
    "get_norms": get_norms,
    "propose_stories": propose_stories,
}
