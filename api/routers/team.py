import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from collections import defaultdict
from jira_client import JiraClient
from effort import extract_effort

router = APIRouter()
templates = Jinja2Templates(directory="templates")
client = JiraClient()
logger = logging.getLogger(__name__)

_EMPTY_BLOCK = {"display": "", "issues": 0, "story_points": 0, "hours": 0.0, "blocked": 0, "by_type": {}}


def _aggregate_by_user(issues: list, sp_field: str) -> dict:
    by_user: dict = defaultdict(lambda: {
        "display": "",
        "issues": 0,
        "story_points": 0,
        "hours": 0.0,
        "blocked": 0,
        "by_type": defaultdict(int),
    })

    for i in issues:
        f = i["fields"]
        assignee = f.get("assignee")
        if not assignee:
            username = "_unassigned"
            display = "Sin asignar"
        else:
            username = assignee.get("name", "_unknown")
            display = assignee.get("displayName", username)

        u = by_user[username]
        u["display"] = display
        u["issues"] += 1
        e = extract_effort(f, sp_field)
        u["story_points"] += e["committed_sp"]
        u["hours"] += e["committed_h"]
        u["by_type"][(f.get("issuetype") or {}).get("name", "Unknown")] += 1
        if (f.get("status") or {}).get("name", "").lower() in ("blocked", "bloqueado"):
            u["blocked"] += 1

    result = {}
    for k, v in by_user.items():
        result[k] = {
            "display": v["display"],
            "issues": v["issues"],
            "story_points": v["story_points"],
            "hours": round(v["hours"], 1),
            "blocked": v["blocked"],
            "by_type": dict(v["by_type"]),
        }
    return result


def _active_sprint_issues(project_key: str) -> list:
    """Issues in the active sprint(s) of every board associated with the
    project. Some boards are shared across many projects (their filter JQL
    spans multiple project keys), so results are filtered back down to this
    project. Issues appearing on more than one board's active sprint are
    deduplicated by key."""
    issues_by_key: dict = {}
    try:
        boards = client.get_boards(project_key)
    except Exception as e:
        logger.error(f"[{project_key}] get_boards failed for sprint scope: {e}")
        return []

    for board in boards:
        try:
            active_sprints = client.get_sprints(board["id"], state="active")
        except Exception as e:
            logger.error(f"[{project_key}] get_sprints failed for board {board['id']}: {e}")
            continue
        for sprint in active_sprints:
            for issue in client.get_sprint_issues(sprint["id"]):
                if (issue["fields"].get("project") or {}).get("key") != project_key:
                    continue
                issues_by_key[issue["key"]] = issue

    return list(issues_by_key.values())


def get_team_data(project_key: str) -> dict:
    empty = {"project": project_key, "users": [], "total_issues": 0}
    try:
        sp_field = client.get_story_points_field()
        backlog_issues = client.search_issues(
            f'project = {project_key} AND resolution = Unresolved',
            fields=["summary", "assignee", "issuetype", "status", "project", sp_field, "priority"],
            max_results=500,
        )
        logger.info(f"[{project_key}] backlog issues: {len(backlog_issues)}")

        sprint_issues = _active_sprint_issues(project_key)
        logger.info(f"[{project_key}] active sprint issues: {len(sprint_issues)}")

        backlog_agg = _aggregate_by_user(backlog_issues, sp_field)
        sprint_agg = _aggregate_by_user(sprint_issues, sp_field)

        usernames = set(backlog_agg) | set(sprint_agg)
        users = {}
        for username in usernames:
            backlog_block = backlog_agg.get(username, _EMPTY_BLOCK)
            sprint_block = sprint_agg.get(username, _EMPTY_BLOCK)
            users[username] = {
                "display": backlog_block["display"] or sprint_block["display"],
                "backlog": backlog_block,
                "sprint": sprint_block,
            }

        sorted_users = sorted(users.items(), key=lambda x: x[1]["backlog"]["issues"], reverse=True)
        return {"project": project_key, "users": sorted_users, "total_issues": len(backlog_issues)}
    except Exception as e:
        logger.error(f"[{project_key}] get_team_data failed: {e}")
        return empty


@router.get("/api/team/{project}")
async def api_team(project: str):
    return get_team_data(project.upper())


@router.get("/dashboard/team", response_class=HTMLResponse)
async def dashboard_team(request: Request, project: str | None = None):
    if not project:
        projects = client.get_all_projects()
        project = projects[0]["key"] if projects else ""
    project = project.upper()
    data = get_team_data(project)
    return templates.TemplateResponse(
        "team.html",
        {"request": request, "selected": project, **data},
    )
