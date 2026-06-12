from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jira_client import JiraClient

router = APIRouter()
templates = Jinja2Templates(directory="templates")
client = JiraClient()

PROJECT_KEYS = ["SCRUM", "CRM", "INF"]


def get_overview_data() -> dict:
    projects_data = []
    total_open = 0
    total_critical_bugs = 0
    total_unassigned = 0
    total_epics_in_progress = 0

    for key in PROJECT_KEYS:
        try:
            proj = client.get_project(key)
        except Exception:
            continue

        open_issues = client.search_issues(
            f'project = {key} AND resolution = Unresolved',
            fields=["summary", "status", "issuetype"],
            max_results=200,
        )
        sprint_issues = client.search_issues(
            f'project = {key} AND sprint in openSprints()',
            fields=["summary", "status", "issuetype"],
            max_results=200,
        )
        sprint_done = [
            i for i in sprint_issues
            if (i["fields"].get("status") or {}).get("name") == "Done"
        ]
        critical_bugs = client.search_issues(
            f'project = {key} AND issuetype = Bug AND priority = Highest AND resolution = Unresolved',
            fields=["summary", "priority"],
            max_results=50,
        )
        unassigned = client.search_issues(
            f'project = {key} AND assignee is EMPTY AND resolution = Unresolved',
            fields=["summary"],
            max_results=50,
        )
        epics_ip = client.search_issues(
            f'project = {key} AND issuetype = Epic AND status = "In Progress"',
            fields=["summary", "status"],
            max_results=20,
        )

        total_open += len(open_issues)
        total_critical_bugs += len(critical_bugs)
        total_unassigned += len(unassigned)
        total_epics_in_progress += len(epics_ip)

        projects_data.append({
            "key": key,
            "name": proj.get("name", key),
            "open_issues": len(open_issues),
            "sprint_total": len(sprint_issues),
            "sprint_done": len(sprint_done),
            "sprint_pct": round(len(sprint_done) / max(len(sprint_issues), 1) * 100),
            "critical_bugs": len(critical_bugs),
            "unassigned": len(unassigned),
            "epics_in_progress": len(epics_ip),
        })

    return {
        "projects": projects_data,
        "total_open": total_open,
        "total_critical_bugs": total_critical_bugs,
        "total_unassigned": total_unassigned,
        "total_epics_in_progress": total_epics_in_progress,
        "active_projects": len(projects_data),
    }


@router.get("/api/overview")
async def api_overview():
    return get_overview_data()


@router.get("/dashboard/overview", response_class=HTMLResponse)
async def dashboard_overview(request: Request):
    data = get_overview_data()
    return templates.TemplateResponse(
        "overview.html", {"request": request, **data}
    )
