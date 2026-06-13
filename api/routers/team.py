from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from collections import defaultdict
from jira_client import JiraClient

router = APIRouter()
templates = Jinja2Templates(directory="templates")
client = JiraClient()


def get_team_data(project_key: str) -> dict:
    empty = {"project": project_key, "users": [], "total_issues": 0}
    try:
        sp_field = client.get_story_points_field()
        issues = client.search_issues(
            f'project = {project_key} AND resolution = Unresolved',
            fields=["summary", "assignee", "issuetype", "status", sp_field, "priority"],
            max_results=500,
        )

        by_user: dict = defaultdict(lambda: {
            "display": "",
            "issues": 0,
            "story_points": 0,
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
            u["story_points"] += f.get(sp_field) or 0
            u["by_type"][(f.get("issuetype") or {}).get("name", "Unknown")] += 1
            if (f.get("status") or {}).get("name", "").lower() in ("blocked", "bloqueado"):
                u["blocked"] += 1

        result = {}
        for k, v in by_user.items():
            result[k] = {
                "display": v["display"],
                "issues": v["issues"],
                "story_points": v["story_points"],
                "blocked": v["blocked"],
                "by_type": dict(v["by_type"]),
            }

        sorted_users = sorted(result.items(), key=lambda x: x[1]["issues"], reverse=True)
        return {"project": project_key, "users": sorted_users, "total_issues": len(issues)}
    except Exception:
        return empty


@router.get("/api/team/{project}")
async def api_team(project: str):
    return get_team_data(project.upper())


@router.get("/dashboard/team", response_class=HTMLResponse)
async def dashboard_team(request: Request, project: str = "DEVOPSSP"):
    project = project.upper()
    data = get_team_data(project)
    return templates.TemplateResponse(
        "team.html",
        {"request": request, "selected": project, **data},
    )
