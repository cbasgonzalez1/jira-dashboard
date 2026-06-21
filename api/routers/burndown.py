import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta, timezone
from jira_client import JiraClient
from constants import DONE_STATUSES

router = APIRouter()
templates = Jinja2Templates(directory="templates")
client = JiraClient()
logger = logging.getLogger(__name__)


def get_burndown_data(project_key: str) -> dict:
    empty = {"project": project_key, "sprint": None, "days": [], "ideal": [], "actual": []}
    try:
        sp_field = client.get_story_points_field()
        boards = client.get_boards(project_key)
        logger.info(f"[{project_key}] boards: {len(boards)}")
        if not boards:
            return empty

        board_id = boards[0]["id"]
        active = client.get_sprints(board_id, state="active")
        logger.info(f"[{project_key}] active sprints: {len(active)}")
        if not active:
            return empty

        sprint = active[0]
        sprint_id = sprint["id"]
        start_str = sprint.get("startDate", "")
        end_str = sprint.get("endDate", "")

        try:
            start = datetime.fromisoformat(start_str.replace("+0000", "+00:00").replace(".000+00:00", "+00:00"))
            end = datetime.fromisoformat(end_str.replace("+0000", "+00:00").replace(".000+00:00", "+00:00"))
        except Exception:
            start = datetime.now(timezone.utc) - timedelta(days=7)
            end = datetime.now(timezone.utc) + timedelta(days=7)

        issues = client.get_sprint_issues(sprint_id)
        logger.info(f"[{project_key}] sprint '{sprint['name']}' issues: {len(issues)}")
        total_pts = sum(i["fields"].get(sp_field) or 0 for i in issues)

        total_days = (end - start).days or 1
        total_days_range = total_days + 1
        days = [(start + timedelta(days=d)).strftime("%m/%d") for d in range(total_days_range)]
        ideal = [round(total_pts - (total_pts * d / total_days), 1) for d in range(total_days_range)]

        done_pts = sum(
            i["fields"].get(sp_field) or 0
            for i in issues
            if (i["fields"].get("status") or {}).get("name", "").lower() in DONE_STATUSES
        )
        today = datetime.now(timezone.utc)
        elapsed = min(max((today - start).days, 0), total_days)

        actual = []
        for d in range(total_days_range):
            if d <= elapsed:
                day_done = done_pts / max(elapsed, 1) if d <= elapsed else 0
                actual.append(max(total_pts - round(day_done * d), 0))
            else:
                actual.append(None)

        return {
            "project": project_key,
            "sprint": sprint["name"],
            "sprint_end": end.strftime("%Y-%m-%d"),
            "total_pts": total_pts,
            "done_pts": done_pts,
            "remaining_pts": total_pts - done_pts,
            "days": days,
            "ideal": ideal,
            "actual": actual,
        }
    except Exception as e:
        logger.error(f"[{project_key}] get_burndown_data failed: {e}")
        return empty


@router.get("/api/burndown/{project}")
async def api_burndown(project: str):
    return get_burndown_data(project.upper())


@router.get("/dashboard/burndown", response_class=HTMLResponse)
async def dashboard_burndown(request: Request, project: str | None = None):
    if not project:
        projects = client.get_all_projects()
        project = projects[0]["key"] if projects else ""
    project = project.upper()
    data = get_burndown_data(project)
    return templates.TemplateResponse(
        "burndown.html",
        {"request": request, "selected": project, **data},
    )
