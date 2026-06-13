import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jira_client import JiraClient

router = APIRouter()
templates = Jinja2Templates(directory="templates")
client = JiraClient()
logger = logging.getLogger(__name__)


def get_overview_data() -> dict:
    empty = {
        "projects": [],
        "total_open": 0,
        "total_critical_bugs": 0,
        "total_unassigned": 0,
        "total_epics_in_progress": 0,
        "active_projects": 0,
    }

    try:
        raw_projects = client.get_all_projects()
        logger.info(f"get_all_projects returned {len(raw_projects)} projects: {[p['key'] for p in raw_projects]}")
    except Exception as e:
        logger.error(f"get_all_projects failed: {e}")
        return empty

    if not raw_projects:
        logger.warning("get_all_projects returned empty list")
        return empty

    projects_data = []
    total_open = 0
    total_critical_bugs = 0
    total_unassigned = 0
    total_epics_in_progress = 0

    for proj_meta in raw_projects[:15]:
        key = proj_meta["key"]
        proj_name = proj_meta.get("name", key)
        try:
            open_issues = client.search_issues(
                f'project = {key} AND resolution = Unresolved',
                fields=["summary", "status", "issuetype"],
                max_results=200,
            )
            logger.info(f"[{key}] open_issues: {len(open_issues)}")

            sprint_issues = client.search_issues(
                f'project = {key} AND sprint in openSprints()',
                fields=["summary", "status", "issuetype"],
                max_results=200,
            )
            logger.info(f"[{key}] sprint_issues: {len(sprint_issues)}")

            sprint_done = [
                i for i in sprint_issues
                if (i["fields"].get("status") or {}).get("name", "").lower() in (
                    "done", "hecho", "cerrado", "resuelto", "closed", "resolved"
                )
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

        except Exception as e:
            logger.error(f"[{key}] search_issues failed: {e}")
            continue

        total_open += len(open_issues)
        total_critical_bugs += len(critical_bugs)
        total_unassigned += len(unassigned)
        total_epics_in_progress += len(epics_ip)

        projects_data.append({
            "key": key,
            "name": proj_name,
            "open_issues": len(open_issues),
            "sprint_total": len(sprint_issues),
            "sprint_done": len(sprint_done),
            "sprint_pct": round(len(sprint_done) / max(len(sprint_issues), 1) * 100),
            "critical_bugs": len(critical_bugs),
            "unassigned": len(unassigned),
            "epics_in_progress": len(epics_ip),
        })

    logger.info(f"overview complete: {len(projects_data)} projects, total_open={total_open}")
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
