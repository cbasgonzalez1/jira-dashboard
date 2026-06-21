import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from jira_client import JiraClient
from config import settings
from constants import DONE_STATUSES, TODO_STATUSES, IN_PROGRESS_STATUSES

router = APIRouter(prefix="/api/sprint-dashboard")
client = JiraClient()
logger = logging.getLogger(__name__)

# ── Status map — English + Spanish ────────────────────────────────────────────
_STATUS_MAP = {
    # todo
    "to do": "todo", "backlog": "todo", "open": "todo",
    "selected for development": "todo",
    "por hacer": "todo", "abierto": "todo",
    # in_progress
    "in progress": "in_progress", "in development": "in_progress",
    "en curso": "in_progress", "en progreso": "in_progress",
    # validation / review
    "in review": "validation", "code review": "validation",
    "testing": "validation", "qa": "validation",
    "in testing": "validation", "review": "validation",
    "validación": "validation", "en revisión": "validation",
    # blocked (counts as work remaining)
    "blocked": "in_progress", "bloqueado": "in_progress",
    # done — source of truth is DONE_STATUSES constant
    **{s: "done" for s in DONE_STATUSES},
}


def _cat(status_name: str) -> str:
    s = status_name.lower().strip()
    if s in DONE_STATUSES:
        return "done"
    return _STATUS_MAP.get(s, "in_progress")


def _h(seconds) -> float:
    return round((seconds or 0) / 3600, 2)


def _parse_dt(s: str, fallback: datetime) -> datetime:
    if not s:
        return fallback
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return fallback


def _sp(fields: dict) -> float:
    """Extract story points: customfield_10002 primary, customfield_11934 fallback."""
    return (
        fields.get("customfield_10002")
        or fields.get("customfield_11934")
        or 0
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/projects")
async def list_projects():
    """All projects accessible to the user via /rest/api/2/project."""
    projects = client.get_all_projects()
    logger.info(f"list_projects: {len(projects)} projects")
    return sorted(
        [{"key": p["key"], "name": p["name"]} for p in projects],
        key=lambda x: x["name"],
    )


@router.get("/boards")
async def list_boards(project_key: str = Query(None)):
    """Boards for a project (when project_key given) or all scrum boards."""
    if project_key:
        raw = client.get_boards(project_key)
    else:
        raw = client.get_all_boards(board_type="scrum")
    logger.info(f"list_boards project_key={project_key}: {len(raw)} boards")
    return [{"id": b["id"], "name": b["name"], "type": b.get("type", "")} for b in raw]


@router.get("/sprints/{board_id}")
async def list_sprints(board_id: int):
    sprints = client.get_sprints(board_id, state="active,closed,future")
    logger.info(f"list_sprints board_id={board_id}: {len(sprints)} sprints")

    def sort_key(s: dict):
        state = s.get("state", "")
        order = {"active": 0, "future": 1, "closed": 2}.get(state, 3)
        id_tie = -s["id"] if state == "closed" else s["id"]
        return (order, id_tie)

    sprints.sort(key=sort_key)
    return [
        {
            "id":         s["id"],
            "name":       s["name"],
            "state":      s["state"],
            "start_date": s.get("startDate", ""),
            "end_date":   s.get("endDate", ""),
        }
        for s in sprints
    ]


@router.get("/data")
async def dashboard_data(board_id: int = Query(...), sprint_id: int = Query(...)):
    now = datetime.now(timezone.utc)

    # ── Sprint metadata ──────────────────────────────────────────────────────
    sprints = client.get_sprints(board_id)
    sprint = next((s for s in sprints if s["id"] == sprint_id), None)
    if not sprint:
        logger.error(f"dashboard_data: sprint {sprint_id} not found on board {board_id}")
        return {
            "error": "Sprint not found",
            "sprint": {}, "kpis": {}, "by_person": [], "by_project": [], "deviations": [],
        }

    start_dt = _parse_dt(sprint.get("startDate", ""), now)
    end_dt   = _parse_dt(sprint.get("endDate", ""),   now)

    days_total     = max((end_dt - start_dt).days, 1)
    days_elapsed   = max(min((now - start_dt).days, days_total), 1)
    days_remaining = max((end_dt - now).days, 0)

    # ── Issues ───────────────────────────────────────────────────────────────
    issues = client.get_sprint_issues_by_jql(sprint_id)
    logger.info(f"dashboard_data sprint={sprint_id}: {len(issues)} issues")

    # ── Aggregate ────────────────────────────────────────────────────────────
    total_original_s = 0
    total_remaining_s = 0
    total_spent_s = 0
    done_sp = 0.0
    total_sp = 0.0
    done_count = 0
    overcost_s = 0

    by_person: dict[str, dict] = {}
    by_project: dict[str, dict] = {}
    deviations: list[dict] = []

    for issue in issues:
        f   = issue.get("fields", {})
        key = issue.get("key", "")

        status_name = (f.get("status") or {}).get("name", "")
        cat = _cat(status_name)

        assignee  = f.get("assignee") or {}
        pid       = assignee.get("name") or assignee.get("accountId") or "_unassigned"
        pname     = assignee.get("displayName", "Unassigned")

        proj      = f.get("project") or {}
        proj_key  = proj.get("key", "UNKNOWN")
        proj_name = proj.get("name", proj_key)

        tt     = f.get("timetracking") or {}
        orig_s = tt.get("originalEstimateSeconds") or f.get("timeoriginalestimate") or 0
        rem_s  = tt.get("remainingEstimateSeconds") or 0
        spent_s= tt.get("timeSpentSeconds") or f.get("timespent") or 0

        sp = _sp(f)

        # Sprint totals
        total_original_s += orig_s
        total_sp         += sp
        total_spent_s    += spent_s

        if cat == "done":
            done_sp    += sp
            done_count += 1
            if orig_s > 0 and spent_s > orig_s:
                overcost_s += spent_s - orig_s
        else:
            total_remaining_s += rem_s

        # Deviation per issue — guard against zero original estimate
        if orig_s == 0 or spent_s == 0:
            pass  # no estimate or no time logged: skip deviation
        else:
            dev_pct = (spent_s - orig_s) / orig_s * 100
            if abs(dev_pct) > 10:
                deviations.append({
                    "key":          key,
                    "summary":      f.get("summary", ""),
                    "original_h":   _h(orig_s),
                    "spent_h":      _h(spent_s),
                    "deviation_pct": round(dev_pct, 1),
                })

        # Per person
        if pid not in by_person:
            by_person[pid] = {
                "name": pname, "account_id": pid,
                "todo": 0.0, "in_progress": 0.0, "validation": 0.0, "done": 0.0,
                "todo_count": 0, "in_progress_count": 0,
                "validation_count": 0, "done_count": 0,
                "remaining_s": 0, "done_sp": 0.0, "projects": set(),
            }
        pp = by_person[pid]
        pp["projects"].add(proj_key)
        pp[f"{cat}_count"] += 1
        if cat == "done":
            pp["done"]    += _h(spent_s)
            pp["done_sp"] += sp
        else:
            pp[cat]           += _h(rem_s)
            pp["remaining_s"] += rem_s

        # Per project
        if proj_key not in by_project:
            by_project[proj_key] = {
                "key": proj_key, "name": proj_name,
                "todo": 0.0, "in_progress": 0.0, "validation": 0.0, "done": 0.0,
                "todo_count": 0, "in_progress_count": 0,
                "validation_count": 0, "done_count": 0,
                "remaining_s": 0, "done_original_s": 0, "done_spent_s": 0,
                "done_sp": 0.0, "total_sp": 0.0, "high_prio_open": 0,
            }
        prj = by_project[proj_key]
        prj["total_sp"]      += sp
        prj[f"{cat}_count"]  += 1
        if cat == "done":
            prj["done"]           += _h(spent_s)
            prj["done_sp"]        += sp
            prj["done_original_s"]+= orig_s
            prj["done_spent_s"]   += spent_s
        else:
            prj[cat]          += _h(rem_s)
            prj["remaining_s"]+= rem_s
            prio_name = (f.get("priority") or {}).get("name", "")
            if prio_name in ("Highest", "High", "Critical", "Blocker"):
                prj["high_prio_open"] += 1

    # ── KPIs ─────────────────────────────────────────────────────────────────
    total_original_h  = _h(total_original_s)
    work_remaining_h  = _h(total_remaining_s)
    work_remaining_pct = (
        round(work_remaining_h / total_original_h * 100, 1) if total_original_h > 0 else 0.0
    )

    team_size            = len([p for p in by_person if p != "_unassigned"])
    capacity_remaining_h = round(
        team_size * settings.work_hours_per_day * days_remaining * settings.team_utilization_factor, 1
    )

    current_work_s  = total_remaining_s + total_spent_s
    deviation_pct   = (
        round((current_work_s - total_original_s) / total_original_s * 100, 1)
        if total_original_s > 0 else 0.0
    )

    achievable_delta      = round(capacity_remaining_h - work_remaining_h, 1)
    velocity_today_sp     = round(done_sp / days_elapsed, 2)
    time_logged_per_day   = round(_h(total_spent_s) / days_elapsed, 2)
    remaining_per_person  = round(work_remaining_h / max(team_size, 1), 1)

    # ── Finalize by_person ───────────────────────────────────────────────────
    by_person_list = sorted(
        [
            {
                "name":               p["name"],
                "account_id":         aid,
                "todo":               round(p["todo"], 2),
                "in_progress":        round(p["in_progress"], 2),
                "validation":         round(p["validation"], 2),
                "done":               round(p["done"], 2),
                "todo_count":         p["todo_count"],
                "in_progress_count":  p["in_progress_count"],
                "validation_count":   p["validation_count"],
                "done_count":         p["done_count"],
                "remaining_h":        _h(p["remaining_s"]),
                "velocity_today":     round(p["done_sp"] / days_elapsed, 2),
                "n_projects":         len(p["projects"]),
            }
            for aid, p in by_person.items()
        ],
        key=lambda x: x["remaining_h"],
        reverse=True,
    )

    # ── Finalize by_project ──────────────────────────────────────────────────
    by_project_list = []
    for prj in by_project.values():
        total_issues = (
            prj["todo_count"] + prj["in_progress_count"]
            + prj["validation_count"] + prj["done_count"]
        )
        dev = 0.0
        if prj["done_original_s"] > 0:
            dev = round(
                (prj["done_spent_s"] - prj["done_original_s"]) / prj["done_original_s"] * 100, 1
            )
        by_project_list.append({
            "key":                  prj["key"],
            "name":                 prj["name"],
            "todo":                 round(prj["todo"], 2),
            "in_progress":          round(prj["in_progress"], 2),
            "validation":           round(prj["validation"], 2),
            "done":                 round(prj["done"], 2),
            "todo_count":           prj["todo_count"],
            "in_progress_count":    prj["in_progress_count"],
            "validation_count":     prj["validation_count"],
            "done_count":           prj["done_count"],
            "remaining_h":          _h(prj["remaining_s"]),
            "deviation_pct":        dev,
            "velocity_today":       round(prj["done_sp"] / days_elapsed, 2),
            "mandatory_incomplete": prj["high_prio_open"],
            "completion_pct":       round(prj["done_count"] / max(total_issues, 1) * 100, 1),
        })
    by_project_list.sort(key=lambda x: x["key"])
    deviations.sort(key=lambda x: abs(x["deviation_pct"]), reverse=True)

    logger.info(
        f"dashboard_data sprint={sprint_id}: done={done_count}/{len(issues)}, "
        f"team_size={team_size}, capacity_remaining={capacity_remaining_h}h"
    )

    return {
        "sprint": {
            "id":         sprint["id"],
            "name":       sprint["name"],
            "state":      sprint["state"],
            "start_date": sprint.get("startDate", ""),
            "end_date":   sprint.get("endDate", ""),
        },
        "kpis": {
            "days_remaining":       days_remaining,
            "days_elapsed":         days_elapsed,
            "days_total":           days_total,
            "work_remaining_h":     work_remaining_h,
            "work_remaining_pct":   work_remaining_pct,
            "capacity_remaining_h": capacity_remaining_h,
            "deviation_pct":        deviation_pct,
            "achievable":           achievable_delta >= 0,
            "achievable_delta_h":   achievable_delta,
            "overcost_h":           _h(overcost_s),
            "velocity_today_sp":    velocity_today_sp,
            "time_logged_per_day_h":time_logged_per_day,
            "remaining_per_person_h": remaining_per_person,
            "team_size":            team_size,
            "done_sp":              done_sp,
            "total_sp":             total_sp,
            "done_issues":          done_count,
            "total_issues":         len(issues),
        },
        "by_person":  by_person_list,
        "by_project": by_project_list,
        "deviations": deviations,
    }
