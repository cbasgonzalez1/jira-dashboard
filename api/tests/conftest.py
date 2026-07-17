"""Shared helpers for building mock Jira objects."""

# Infers statusCategory.key from the literal status name used across existing
# tests, so make_issue(status="Done") still produces a realistic fixture
# without every call site having to pass category explicitly.
_STATUS_TO_CATEGORY_KEY = {
    "done": "done",
    "resolved": "done",
    "closed": "done",
    "to do": "new",
    "open": "new",
    "backlog": "new",
    "in progress": "indeterminate",
    "blocked": "indeterminate",
}


def make_issue(
    status="Open",
    itype="Story",
    assignee_name=None,
    assignee_display=None,
    sp=None,
    orig_s=0,
    rem_s=0,
    spent_s=0,
    priority="Medium",
    project_key="PROJ",
    project_name="Project",
    key="PROJ-1",
    category=None,
):
    assignee = None
    if assignee_name:
        assignee = {"name": assignee_name, "displayName": assignee_display or assignee_name, "accountId": assignee_name}

    category_key = category or _STATUS_TO_CATEGORY_KEY.get(status.lower(), "indeterminate")

    return {
        "key": key,
        "fields": {
            "summary": f"Issue {key}",
            "status": {"name": status, "statusCategory": {"key": category_key}},
            "issuetype": {"name": itype},
            "assignee": assignee,
            "priority": {"name": priority},
            "project": {"key": project_key, "name": project_name},
            "customfield_10002": sp,
            "customfield_11934": None,
            "timetracking": {
                "originalEstimateSeconds": orig_s,
                "remainingEstimateSeconds": rem_s,
                "timeSpentSeconds": spent_s,
            },
            "timespent": spent_s,
            "timeoriginalestimate": orig_s,
        },
    }


def make_sprint(sid=1, name="Sprint 1", state="active",
                start="2026-06-01T00:00:00+00:00",
                end="2026-06-14T00:00:00+00:00"):
    return {"id": sid, "name": name, "state": state, "startDate": start, "endDate": end}


def make_board(bid=1, name="Board 1", btype="scrum"):
    return {"id": bid, "name": name, "type": btype}
