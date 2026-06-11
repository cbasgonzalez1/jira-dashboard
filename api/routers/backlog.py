from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from collections import Counter
from jira_client import JiraClient

router = APIRouter()
templates = Jinja2Templates(directory="templates")
client = JiraClient()

PROJECT_KEYS = ["SCRUM", "CRM", "INF"]


def get_backlog_data(project_key: str) -> dict:
    sp_field = client.get_story_points_field()
    issues = client.search_issues(
        f'project = {project_key} AND resolution = Unresolved AND sprint not in openSprints()',
        fields=["summary", "issuetype", "priority", "status", sp_field],
        max_results=500,
    )

    by_type: Counter = Counter()
    by_priority: Counter = Counter()
    by_status: Counter = Counter()
    unestimated = 0

    for i in issues:
        f = i["fields"]
        by_type[f["issuetype"]["name"]] += 1
        by_priority[f.get("priority", {}).get("name", "None")] += 1
        by_status[f["status"]["name"]] += 1
        pts = f.get(sp_field)
        if not pts:
            unestimated += 1

    return {
        "project": project_key,
        "total": len(issues),
        "unestimated": unestimated,
        "by_type": dict(by_type),
        "by_priority": dict(by_priority),
        "by_status": dict(by_status),
    }


@router.get("/api/backlog/{project}")
async def api_backlog(project: str):
    return get_backlog_data(project.upper())


@router.get("/dashboard/backlog", response_class=HTMLResponse)
async def dashboard_backlog(request: Request, project: str = "SCRUM"):
    project = project.upper()
    data = get_backlog_data(project)
    return templates.TemplateResponse(
        "backlog.html",
        {"request": request, "project_keys": PROJECT_KEYS, "selected": project, **data},
    )
