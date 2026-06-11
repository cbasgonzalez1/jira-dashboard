from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta, timezone
from jira_client import JiraClient

router = APIRouter()
templates = Jinja2Templates(directory="templates")
client = JiraClient()

PROJECT_KEYS = ["SCRUM", "CRM"]


def get_burndown_data(project_key: str) -> dict:
    sp_field = client.get_story_points_field()
    boards = client.get_boards(project_key)
    if not boards:
        return {"project": project_key, "sprint": None, "days": [], "ideal": [], "actual": []}

    board_id = boards[0]["id"]
    active = client.get_sprints(board_id, state="active")
    if not active:
        return {"project": project_key, "sprint": None, "days": [], "ideal": [], "actual": []}

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
    total_pts = sum(i["fields"].get(sp_field) or 0 for i in issues)

    # Build day axis
    total_days = (end - start).days or 1
    days = [(start + timedelta(days=d)).strftime("%m/%d") for d in range(total_days + 1)]

    # Ideal burndown: linear from total_pts to 0
    ideal = [
        round(total_pts - (total_pts * d / total_days), 1)
        for d in range(total_days + 1)
    ]

    # Actual: simulate based on Done issues (simplified — we don't have per-day history)
    done_pts = sum(
        i["fields"].get(sp_field) or 0
        for i in issues
        if i["fields"]["status"]["name"] == "Done"
    )
    today = datetime.now(timezone.utc)
    elapsed = max((today - start).days, 0)
    elapsed = min(elapsed, total_days)

    actual = []
    remaining = total_pts
    for d in range(total_days + 1):
        if d <= elapsed:
            # Linear approximation of done work
            day_done = done_pts / max(elapsed, 1) if d <= elapsed else 0
            remaining_today = total_pts - round(day_done * d)
            actual.append(max(remaining_today, 0))
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


@router.get("/api/burndown/{project}")
async def api_burndown(project: str):
    return get_burndown_data(project.upper())


@router.get("/dashboard/burndown", response_class=HTMLResponse)
async def dashboard_burndown(request: Request, project: str = "SCRUM"):
    project = project.upper()
    data = get_burndown_data(project)
    return templates.TemplateResponse(
        "burndown.html",
        {"request": request, "project_keys": PROJECT_KEYS, "selected": project, **data},
    )
