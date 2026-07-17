import logging
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jira_client import JiraClient
from status_category import categorize

router = APIRouter()
templates = Jinja2Templates(directory="templates")
client = JiraClient()
logger = logging.getLogger(__name__)


def _fetch_project_data(proj_meta: dict) -> dict | None:
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
            f'project = {key} AND sprint in openSprints() AND issuetype != Epic',
            fields=["summary", "status", "issuetype"],
            max_results=200,
        )
        logger.info(f"[{key}] sprint_issues: {len(sprint_issues)}")

        sprint_done = [
            i for i in sprint_issues
            if categorize(i["fields"].get("status") or {}) == "done"
        ]

        critical_bugs = client.search_issues(
            f'project = {key} AND issuetype = Bug AND priority = Highest AND resolution = Unresolved',
            fields=["summary", "priority"],
            max_results=50,
        )
        logger.info(f"[{key}] critical_bugs: {len(critical_bugs)}")

        unassigned = client.search_issues(
            f'project = {key} AND assignee is EMPTY AND resolution = Unresolved AND issuetype != Epic',
            fields=["summary"],
            max_results=50,
        )
        logger.info(f"[{key}] unassigned: {len(unassigned)}")

        # statusCategory (not status) — its "In Progress" name is a stable
        # English identifier independent of the workflow's localized status
        # names (e.g. "En progreso"), unlike a literal status match.
        epics_ip = client.search_issues(
            f'project = {key} AND issuetype = Epic AND statusCategory = "In Progress"',
            fields=["summary", "status"],
            max_results=20,
        )
        logger.info(f"[{key}] epics_in_progress: {len(epics_ip)}")

        return {
            "key": key,
            "name": proj_name,
            "open_issues": len(open_issues),
            "sprint_total": len(sprint_issues),
            "sprint_done": len(sprint_done),
            "sprint_pct": round(len(sprint_done) / max(len(sprint_issues), 1) * 100),
            "critical_bugs": len(critical_bugs),
            "unassigned": len(unassigned),
            "epics_in_progress": len(epics_ip),
        }
    except Exception as e:
        logger.error(f"[{key}] data fetch failed: {e}")
        return None


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

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(_fetch_project_data, raw_projects))

    projects_data = [r for r in results if r is not None]

    total_open = sum(p["open_issues"] for p in projects_data)
    total_critical_bugs = sum(p["critical_bugs"] for p in projects_data)
    total_unassigned = sum(p["unassigned"] for p in projects_data)
    total_epics_in_progress = sum(p["epics_in_progress"] for p in projects_data)

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
