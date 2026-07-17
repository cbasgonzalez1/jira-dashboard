import logging
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta, timezone
from jira_client import JiraClient
from status_category import categorize
from effort import extract_effort

router = APIRouter()
templates = Jinja2Templates(directory="templates")
client = JiraClient()
logger = logging.getLogger(__name__)


def get_burndown_data(project_key: str, board_id: int | None = None, sprint_id: int | None = None) -> dict:
    empty = {"project": project_key, "sprint": None, "days": [], "ideal": [], "actual": []}
    try:
        sp_field = client.get_story_points_field()
        boards = client.get_boards(project_key)
        logger.info(f"[{project_key}] boards: {len(boards)}")
        if not boards:
            return empty

        if board_id is not None and any(b["id"] == board_id for b in boards):
            selected_board_id = board_id
        else:
            # No explicit board_id (or it doesn't belong to this project):
            # fall back to the first board Jira returns. Some boards here
            # are shared across many projects — pick a board explicitly for
            # project-accurate results.
            selected_board_id = boards[0]["id"]

        if sprint_id is not None:
            all_sprints = client.get_sprints(selected_board_id)
            sprint = next((s for s in all_sprints if s["id"] == sprint_id), None)
            if not sprint:
                logger.error(f"[{project_key}] sprint_id {sprint_id} not found on board {selected_board_id}")
                return empty
        else:
            active = client.get_sprints(selected_board_id, state="active")
            logger.info(f"[{project_key}] active sprints: {len(active)}")
            if not active:
                return empty
            sprint = active[0]

        selected_sprint_id = sprint["id"]
        start_str = sprint.get("startDate", "")
        end_str = sprint.get("endDate", "")

        try:
            start = datetime.fromisoformat(start_str.replace("+0000", "+00:00").replace(".000+00:00", "+00:00"))
            end = datetime.fromisoformat(end_str.replace("+0000", "+00:00").replace(".000+00:00", "+00:00"))
        except Exception:
            start = datetime.now(timezone.utc) - timedelta(days=7)
            end = datetime.now(timezone.utc) + timedelta(days=7)

        issues = client.get_sprint_issues(selected_sprint_id)
        logger.info(f"[{project_key}] sprint '{sprint['name']}' issues: {len(issues)}")

        # Hours (timetracking) are the primary metric — most teams in this
        # org estimate/log work in hours, not story points.
        total_h = 0.0
        done_h = 0.0
        total_sp = 0.0
        done_sp = 0.0
        for i in issues:
            f = i["fields"]
            e = extract_effort(f, sp_field)
            total_h += e["committed_h"]
            total_sp += e["committed_sp"]
            if categorize(f.get("status") or {}) == "done":
                done_h += e["spent_h"]
                done_sp += e["committed_sp"]
        total_h = round(total_h, 1)
        done_h = round(done_h, 1)
        total_sp = round(total_sp, 1)
        done_sp = round(done_sp, 1)

        total_days = (end - start).days or 1
        total_days_range = total_days + 1
        days = [(start + timedelta(days=d)).strftime("%m/%d") for d in range(total_days_range)]
        ideal = [round(total_h - (total_h * d / total_days), 1) for d in range(total_days_range)]

        today = datetime.now(timezone.utc)
        elapsed = min(max((today - start).days, 0), total_days)

        actual = []
        for d in range(total_days_range):
            if d <= elapsed:
                day_done = done_h / max(elapsed, 1) if d <= elapsed else 0
                actual.append(max(total_h - round(day_done * d, 1), 0))
            else:
                actual.append(None)

        return {
            "project": project_key,
            "board_id": selected_board_id,
            "sprint": sprint["name"],
            "sprint_end": end.strftime("%Y-%m-%d"),
            # Hours are primary; *_pts kept as aliases so the existing JSON
            # contract (and any consumer reading total_pts/done_pts) keeps working.
            "total_h": total_h,
            "done_h": done_h,
            "remaining_h": round(total_h - done_h, 1),
            "total_pts": total_h,
            "done_pts": done_h,
            "remaining_pts": round(total_h - done_h, 1),
            "total_sp": total_sp,
            "done_sp": done_sp,
            "days": days,
            "ideal": ideal,
            "actual": actual,
        }
    except Exception as e:
        logger.error(f"[{project_key}] get_burndown_data failed: {e}")
        return empty


@router.get("/api/burndown/{project}")
async def api_burndown(project: str, board_id: int | None = Query(None), sprint_id: int | None = Query(None)):
    return get_burndown_data(project.upper(), board_id, sprint_id)


@router.get("/dashboard/burndown", response_class=HTMLResponse)
async def dashboard_burndown(
    request: Request,
    project: str | None = None,
    board_id: int | None = Query(None),
    sprint_id: int | None = Query(None),
):
    if not project:
        projects = client.get_all_projects()
        project = projects[0]["key"] if projects else ""
    project = project.upper()
    data = get_burndown_data(project, board_id, sprint_id)
    return templates.TemplateResponse(
        "burndown.html",
        {"request": request, "selected": project, **data},
    )
