import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jira_client import JiraClient
from config import settings
from constants import DONE_STATUSES

router = APIRouter()
templates = Jinja2Templates(directory="templates")
client = JiraClient()
logger = logging.getLogger(__name__)


def get_velocity_data(project_key: str) -> dict:
    empty = {"project": project_key, "sprints": [], "avg_velocity": 0}
    try:
        sp_field = client.get_story_points_field()
        boards = client.get_boards(project_key)
        logger.info(f"[{project_key}] boards: {len(boards)}")
        if not boards:
            return empty

        board_id = boards[0]["id"]
        # standard rolling window for average velocity; configurable via VELOCITY_SPRINT_WINDOW
        closed_sprints = client.get_sprints(board_id, state="closed")[-settings.velocity_sprint_window:]
        active_sprints = client.get_sprints(board_id, state="active")
        logger.info(f"[{project_key}] closed_sprints (window={settings.velocity_sprint_window}): {len(closed_sprints)}, active: {len(active_sprints)}")

        sprint_data = []
        for sprint in closed_sprints:
            issues = client.get_sprint_issues(sprint["id"])
            logger.info(f"[{project_key}] sprint '{sprint['name']}' issues: {len(issues)}")
            committed = sum(i["fields"].get(sp_field) or 0 for i in issues)
            completed = sum(
                i["fields"].get(sp_field) or 0
                for i in issues
                if (i["fields"].get("status") or {}).get("name", "").lower() in DONE_STATUSES
            )
            sprint_data.append({"name": sprint["name"], "committed": committed, "completed": completed, "state": "closed"})

        for sprint in active_sprints:
            issues = client.get_sprint_issues(sprint["id"])
            logger.info(f"[{project_key}] active sprint '{sprint['name']}' issues: {len(issues)}")
            committed = sum(i["fields"].get(sp_field) or 0 for i in issues)
            completed = sum(
                i["fields"].get(sp_field) or 0
                for i in issues
                if (i["fields"].get("status") or {}).get("name", "").lower() in DONE_STATUSES
            )
            sprint_data.append({"name": sprint["name"], "committed": committed, "completed": completed, "state": "active"})

        closed_completed = [s["completed"] for s in sprint_data if s["state"] == "closed"]
        avg_velocity = round(sum(closed_completed) / max(len(closed_completed), 1))

        return {"project": project_key, "sprints": sprint_data, "avg_velocity": avg_velocity}
    except Exception as e:
        logger.error(f"[{project_key}] get_velocity_data failed: {e}")
        return empty


@router.get("/api/velocity/{project}")
async def api_velocity(project: str):
    return get_velocity_data(project.upper())


@router.get("/dashboard/velocity", response_class=HTMLResponse)
async def dashboard_velocity(request: Request, project: str | None = None):
    if not project:
        projects = client.get_all_projects()
        project = projects[0]["key"] if projects else ""
    project = project.upper()
    data = get_velocity_data(project)
    return templates.TemplateResponse(
        "velocity.html",
        {"request": request, "selected": project, **data},
    )
