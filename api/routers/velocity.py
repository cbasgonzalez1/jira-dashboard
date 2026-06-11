from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jira_client import JiraClient

router = APIRouter()
templates = Jinja2Templates(directory="templates")
client = JiraClient()

PROJECT_KEYS = ["SCRUM", "CRM"]


def get_velocity_data(project_key: str) -> dict:
    sp_field = client.get_story_points_field()
    boards = client.get_boards(project_key)
    if not boards:
        return {"project": project_key, "sprints": [], "avg_velocity": 0}

    board_id = boards[0]["id"]
    closed_sprints = client.get_sprints(board_id, state="closed")[-3:]
    active_sprints = client.get_sprints(board_id, state="active")

    sprint_data = []
    for sprint in closed_sprints:
        issues = client.get_sprint_issues(sprint["id"])
        committed = sum(
            i["fields"].get(sp_field) or 0 for i in issues
        )
        completed = sum(
            i["fields"].get(sp_field) or 0
            for i in issues
            if i["fields"]["status"]["name"] == "Done"
        )
        sprint_data.append({
            "name": sprint["name"],
            "committed": committed,
            "completed": completed,
            "state": "closed",
        })

    for sprint in active_sprints:
        issues = client.get_sprint_issues(sprint["id"])
        committed = sum(i["fields"].get(sp_field) or 0 for i in issues)
        completed = sum(
            i["fields"].get(sp_field) or 0
            for i in issues
            if i["fields"]["status"]["name"] == "Done"
        )
        sprint_data.append({
            "name": sprint["name"],
            "committed": committed,
            "completed": completed,
            "state": "active",
        })

    closed_completed = [s["completed"] for s in sprint_data if s["state"] == "closed"]
    avg_velocity = round(sum(closed_completed) / max(len(closed_completed), 1))

    return {
        "project": project_key,
        "sprints": sprint_data,
        "avg_velocity": avg_velocity,
    }


@router.get("/api/velocity/{project}")
async def api_velocity(project: str):
    return get_velocity_data(project.upper())


@router.get("/dashboard/velocity", response_class=HTMLResponse)
async def dashboard_velocity(request: Request, project: str = "SCRUM"):
    project = project.upper()
    data = get_velocity_data(project)
    return templates.TemplateResponse(
        "velocity.html",
        {"request": request, "project_keys": PROJECT_KEYS, "selected": project, **data},
    )
