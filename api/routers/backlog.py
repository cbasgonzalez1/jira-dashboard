import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from collections import Counter
from jira_client import JiraClient

router = APIRouter()
templates = Jinja2Templates(directory="templates")
client = JiraClient()
logger = logging.getLogger(__name__)


def get_backlog_data(project_key: str) -> dict:
    empty = {"project": project_key, "total": 0, "unestimated": 0, "by_type": {}, "by_priority": {}, "by_status": {}}
    try:
        sp_field = client.get_story_points_field()
        issues = client.search_issues(
            f'project = {project_key} AND resolution = Unresolved AND sprint not in openSprints()',
            fields=["summary", "issuetype", "priority", "status", sp_field],
            max_results=500,
        )
        logger.info(f"[{project_key}] backlog issues: {len(issues)}")

        by_type: Counter = Counter()
        by_priority: Counter = Counter()
        by_status: Counter = Counter()
        unestimated = 0

        for i in issues:
            f = i["fields"]
            by_type[(f.get("issuetype") or {}).get("name", "Unknown")] += 1
            by_priority[(f.get("priority") or {}).get("name", "None")] += 1
            by_status[(f.get("status") or {}).get("name", "Unknown")] += 1
            if not f.get(sp_field):
                unestimated += 1

        return {
            "project": project_key,
            "total": len(issues),
            "unestimated": unestimated,
            "by_type": dict(by_type),
            "by_priority": dict(by_priority),
            "by_status": dict(by_status),
        }
    except Exception as e:
        logger.error(f"[{project_key}] get_backlog_data failed: {e}")
        return empty


@router.get("/api/backlog/{project}")
async def api_backlog(project: str):
    return get_backlog_data(project.upper())


@router.get("/dashboard/backlog", response_class=HTMLResponse)
async def dashboard_backlog(request: Request, project: str | None = None):
    if not project:
        projects = client.get_all_projects()
        project = projects[0]["key"] if projects else ""
    project = project.upper()
    data = get_backlog_data(project)
    return templates.TemplateResponse(
        "backlog.html",
        {"request": request, "selected": project, **data},
    )
