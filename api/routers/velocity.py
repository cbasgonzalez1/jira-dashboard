import logging
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jira_client import JiraClient
from config import settings
from status_category import categorize
from effort import extract_effort

router = APIRouter()
templates = Jinja2Templates(directory="templates")
client = JiraClient()
logger = logging.getLogger(__name__)


def _sprint_effort(issues: list, sp_field: str, project_key: str) -> dict:
    committed_h = 0.0
    done_h = 0.0
    committed_sp = 0.0
    done_sp = 0.0
    for i in issues:
        f = i["fields"]
        # Many boards in this Jira are shared across several projects (their
        # filter JQL spans multiple project keys), so a sprint's issues can
        # belong to other projects too — filter back down to this one.
        if (f.get("project") or {}).get("key") != project_key:
            continue
        e = extract_effort(f, sp_field)
        committed_h += e["committed_h"]
        committed_sp += e["committed_sp"]
        if categorize(f.get("status") or {}) == "done":
            done_h += e["spent_h"]
            done_sp += e["committed_sp"]
    return {
        "committed_h": round(committed_h, 1),
        "done_h": round(done_h, 1),
        "committed_sp": round(committed_sp, 1),
        "done_sp": round(done_sp, 1),
    }


def get_velocity_data(project_key: str, board_id: int | None = None) -> dict:
    empty = {"project": project_key, "sprints": [], "avg_velocity": 0}
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
            # are shared across many projects (their filter JQL spans
            # multiple project keys) — pick a board explicitly for
            # project-accurate results.
            selected_board_id = boards[0]["id"]

        # standard rolling window for average velocity; configurable via VELOCITY_SPRINT_WINDOW
        closed_sprints = client.get_sprints(selected_board_id, state="closed")[-settings.velocity_sprint_window:]
        active_sprints = client.get_sprints(selected_board_id, state="active")
        logger.info(f"[{project_key}] closed_sprints (window={settings.velocity_sprint_window}): {len(closed_sprints)}, active: {len(active_sprints)}")

        sprint_data = []
        for state, sprints in (("closed", closed_sprints), ("active", active_sprints)):
            for sprint in sprints:
                issues = client.get_board_sprint_issues(selected_board_id, sprint["id"])
                logger.info(f"[{project_key}] {state} sprint '{sprint['name']}' issues: {len(issues)}")
                effort = _sprint_effort(issues, sp_field, project_key)
                sprint_data.append({
                    "name": sprint["name"],
                    "state": state,
                    # Hours (timetracking) are the primary metric — most teams in
                    # this org estimate/log work in hours, not story points.
                    "committed": effort["committed_h"],
                    "completed": effort["done_h"],
                    "committed_sp": effort["committed_sp"],
                    "completed_sp": effort["done_sp"],
                })

        closed_completed = [s["completed"] for s in sprint_data if s["state"] == "closed"]
        avg_velocity = round(sum(closed_completed) / max(len(closed_completed), 1), 1)

        closed_completed_sp = [s["completed_sp"] for s in sprint_data if s["state"] == "closed"]
        avg_velocity_sp = (
            round(sum(closed_completed_sp) / max(len(closed_completed_sp), 1), 1)
            if any(closed_completed_sp) else 0
        )

        return {
            "project": project_key,
            "board_id": selected_board_id,
            "sprints": sprint_data,
            "avg_velocity": avg_velocity,
            "avg_velocity_sp": avg_velocity_sp,
        }
    except Exception as e:
        logger.error(f"[{project_key}] get_velocity_data failed: {e}")
        return empty


@router.get("/api/velocity/{project}")
async def api_velocity(project: str, board_id: int | None = Query(None)):
    return get_velocity_data(project.upper(), board_id)


@router.get("/dashboard/velocity", response_class=HTMLResponse)
async def dashboard_velocity(request: Request, project: str | None = None, board_id: int | None = Query(None)):
    if not project:
        projects = client.get_all_projects()
        project = projects[0]["key"] if projects else ""
    project = project.upper()
    data = get_velocity_data(project, board_id)
    return templates.TemplateResponse(
        "velocity.html",
        {"request": request, "selected": project, **data},
    )
