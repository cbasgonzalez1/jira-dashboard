"""
Seed script — injects realistic Jira Cloud data for MDA Portal project.
Run: docker compose exec api python seed/seed_data.py
"""
import sys
import time
import random
import httpx
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table

from jira_client import JiraClient

console = Console()
client = JiraClient()

# ── Config ─────────────────────────────────────────────────────────────────────

ADMIN_ACCOUNT_ID = "712020:5a6edd22-f095-4aa2-a6c3-cc770425c7be"
EXISTING_PROJECT_KEY = "SCRUM"

PROJECTS_TO_CREATE = [
    {"key": "CRM", "name": "CRM & Admissions System"},
    {"key": "INF", "name": "Infrastructure & DevOps"},
]

STORY_POINTS_FIELD = None  # resolved at runtime

SLEEP = 0.35  # seconds between API calls (rate limit safety)

# ── Issue data ──────────────────────────────────────────────────────────────────

EPICS_BY_PROJECT = {
    "SCRUM": [
        "User Authentication & Security",
        "Dashboard & Reporting",
        "API Integration Layer",
        "Mobile Responsive Design",
        "Performance Optimization",
    ],
    "CRM": [
        "Lead Management Pipeline",
        "Application Form Workflow",
        "Automated Email Campaigns",
        "Reporting & Analytics Module",
        "Integration with Payment Gateway",
    ],
    "INF": [
        "Kubernetes Cluster Setup",
        "CI/CD Pipeline Automation",
        "Monitoring & Alerting Stack",
        "Secrets Management Rollout",
        "Database Backup & Recovery",
    ],
}

STORIES_BY_PROJECT = {
    "SCRUM": [
        ("As a student, I can submit my application online", 5),
        ("As an admin, I can review pending applications", 3),
        ("As a user, I can reset my password via email", 2),
        ("As a designer, I can upload portfolio files", 3),
        ("As an admin, I can generate enrollment reports", 5),
        ("As a student, I can view my course schedule", 2),
        ("As a user, I can update my profile picture", 1),
        ("As an admin, I can export student data to CSV", 3),
        ("As a student, I can track application status", 2),
        ("As an admin, I can send bulk notification emails", 5),
        ("As a student, I can view available courses", 3),
        ("As a user, I can change my account password", 1),
        ("As an admin, I can manage user roles", 5),
        ("As a student, I can enroll in a course", 3),
        ("As a student, I can view my grades", 2),
        ("As an admin, I can configure email templates", 3),
        ("As a student, I can download my certificate", 2),
        ("As a user, I can set notification preferences", 2),
        ("As an admin, I can view analytics dashboard", 8),
        ("As a student, I can submit assignments", 3),
        ("As a student, I can message my instructor", 2),
        ("As an admin, I can manage course catalog", 5),
        ("As a student, I can view upcoming deadlines", 2),
        ("As an admin, I can create scholarship applications", 5),
        ("As a student, I can access learning materials", 3),
        ("As an admin, I can review payment history", 3),
        ("As a student, I can rate completed courses", 1),
        ("As an admin, I can configure SSO settings", 8),
        ("As a student, I can join live classes", 5),
        ("As an admin, I can archive completed courses", 2),
    ],
    "CRM": [
        ("Build lead capture form with validation", 3),
        ("Implement lead scoring algorithm", 5),
        ("Create admissions kanban board view", 5),
        ("Add automated follow-up email sequences", 5),
        ("Build document upload and verification portal", 3),
        ("Implement interview scheduling calendar", 5),
        ("Create enrollment confirmation workflow", 3),
        ("Add CRM contact import from CSV", 3),
        ("Build conversion funnel report", 5),
        ("Implement duplicate lead detection", 3),
        ("Create custom field editor for leads", 3),
        ("Add bulk action support on lead list", 5),
        ("Build drag-and-drop email template editor", 8),
        ("Implement A/B testing for email campaigns", 8),
        ("Create agent performance dashboard", 5),
        ("Add payment plan calculator widget", 3),
        ("Build refund request workflow", 3),
        ("Implement waitlist management system", 5),
        ("Create term and cohort management page", 5),
        ("Add SLA tracking for agent responses", 3),
        ("Build parent/guardian contact portal", 5),
        ("Implement multi-language UI support", 8),
        ("Create scholarship application flow", 5),
        ("Add compliance document checklist", 3),
        ("Build API webhook for CRM events", 5),
        ("Implement smart lead assignment rules", 5),
        ("Create admission interview scorecard", 3),
        ("Add e-signature capture for contracts", 5),
        ("Build alumni portal integration", 8),
        ("Implement GDPR data export tool", 5),
    ],
    "INF": [
        ("Set up Helm charts for all microservices", 5),
        ("Configure horizontal pod autoscaling", 3),
        ("Implement blue-green deployment strategy", 5),
        ("Set up Prometheus metrics scraping", 3),
        ("Configure Grafana dashboard templates", 3),
        ("Implement log aggregation with Loki", 5),
        ("Set up HashiCorp Vault for secrets", 5),
        ("Configure RBAC policies for cluster", 5),
        ("Implement automated database snapshots", 3),
        ("Set up staging environment parity", 5),
        ("Configure Kubernetes network policies", 3),
        ("Implement container image vulnerability scanning", 5),
        ("Set up PagerDuty on-call rotation", 2),
        ("Configure CDN for static asset delivery", 3),
        ("Implement AWS cost allocation tagging", 3),
        ("Set up disaster recovery runbook", 5),
        ("Configure WAF rules for API endpoints", 5),
        ("Implement zero-downtime database migrations", 8),
        ("Set up SAST/DAST in CI pipeline", 5),
        ("Configure multi-region failover", 8),
        ("Implement GitOps workflow with ArgoCD", 5),
        ("Set up k6 performance load testing", 3),
        ("Configure Redis cluster for caching", 5),
        ("Implement feature flag service", 3),
        ("Set up SOC2 compliance audit logging", 5),
        ("Configure secrets rotation automation", 5),
        ("Implement API rate limiting middleware", 3),
        ("Set up Statuspage integration", 2),
        ("Configure backup retention policies", 2),
        ("Implement Istio service mesh", 8),
    ],
}

BUGS_BY_PROJECT = {
    "SCRUM": [
        ("Login page crashes on mobile Safari 16", "Highest"),
        ("Session token not invalidated on logout", "Highest"),
        ("Password reset link expires in 1 minute instead of 1 hour", "Highest"),
        ("Application form loses data on browser back button", "High"),
        ("File upload silently fails for files over 5MB", "High"),
        ("Grade calculation rounding error for decimal points", "High"),
        ("Profile image not displayed after upload", "High"),
        ("Calendar shows events in wrong timezone", "High"),
        ("Search returns duplicate results on page 2", "Medium"),
        ("Notification badge count not decremented on read", "Medium"),
        ("PDF certificate missing student signature field", "Medium"),
        ("Course enrollment button unresponsive on Firefox", "Medium"),
        ("Email verification not sent to .edu addresses", "Medium"),
        ("Progress bar shows 101% on completion", "Low"),
        ("Dark mode toggle flickers on page load", "Low"),
    ],
    "CRM": [
        ("Lead import crashes with UTF-8 special characters", "Highest"),
        ("Duplicate leads created on form double-submit", "Highest"),
        ("Email campaign sends to unsubscribed contacts", "Highest"),
        ("Payment installment calculation off by one cent", "High"),
        ("Document upload silently fails for PDF over 10MB", "High"),
        ("Interview calendar allows double-booking same slot", "High"),
        ("Pipeline stage drag-drop broken on Firefox 120", "High"),
        ("Contact merge loses all custom field data", "High"),
        ("Webhook not firing on lead status change to Won", "Medium"),
        ("Bulk email action ignores leads on pages 2 and beyond", "Medium"),
        ("Agent assignment resets to unassigned on page refresh", "Medium"),
        ("Report date range off by one day due to timezone", "Medium"),
        ("CSV export truncates notes longer than 255 chars", "Medium"),
        ("SLA timer does not pause on weekends", "Low"),
        ("Alumni portal shows wrong student display name", "Low"),
    ],
    "INF": [
        ("Kubernetes pod OOM killed during peak traffic", "Highest"),
        ("Vault token renewal race condition causes 401s", "Highest"),
        ("Secret rotation breaks running app containers", "Highest"),
        ("Backup job silently skips empty databases", "High"),
        ("Prometheus scrape timeout on high-load nodes", "High"),
        ("ArgoCD sync stuck after repo merge conflict", "High"),
        ("Redis eviction triggers cache stampede under load", "High"),
        ("Network policy blocks internal health check endpoints", "High"),
        ("CI pipeline fails intermittently on parallel test runs", "Medium"),
        ("Grafana alert fires false positives after deploy", "Medium"),
        ("CDN cache not invalidated after new deployment", "Medium"),
        ("Load balancer drops WebSocket connections after 60s", "Medium"),
        ("Log rotation not cleaning files older than 30 days", "Medium"),
        ("Staging DB schema out of sync with production", "Low"),
        ("PagerDuty integration sends duplicate alert pages", "Low"),
    ],
}

TASKS_BY_PROJECT = {
    "SCRUM": [
        ("Upgrade React to v18 and update all hooks", 3),
        ("Migrate CSS Modules to Tailwind CSS", 5),
        ("Write unit tests for authentication module", 3),
        ("Configure ESLint and Prettier rules", 1),
        ("Set up Storybook for UI component library", 3),
        ("Optimize JavaScript bundle size", 3),
        ("Write API integration test suite", 5),
        ("Update Node.js to LTS version 20", 1),
        ("Document all REST API endpoints in Swagger", 2),
        ("Conduct accessibility audit (WCAG 2.1 AA)", 3),
    ],
    "CRM": [
        ("Upgrade Django to 5.x and fix deprecations", 3),
        ("Migrate database to PostgreSQL 16", 5),
        ("Write unit tests for Celery async tasks", 3),
        ("Refactor authentication middleware", 5),
        ("Configure Redis for Django session caching", 2),
        ("Write E2E tests for lead pipeline flow", 5),
        ("Set up code coverage reporting in CI", 2),
        ("Migrate legacy raw SQL queries to ORM", 5),
        ("Document CRM API endpoints with examples", 2),
        ("Conduct security audit of file upload handling", 3),
    ],
    "INF": [
        ("Audit all IAM roles and remove unused permissions", 3),
        ("Update Terraform modules to latest versions", 3),
        ("Write incident response runbook", 2),
        ("Prune and archive old Docker images from registry", 1),
        ("Upgrade Kubernetes cluster to version 1.30", 5),
        ("Rotate all service account credentials", 2),
        ("Update architecture diagrams in Confluence", 2),
        ("Set up AWS cost anomaly detection alerts", 2),
        ("Review and tighten egress firewall rules", 3),
        ("Archive and document decommissioned services", 2),
    ],
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def sp_field() -> str:
    global STORY_POINTS_FIELD
    if STORY_POINTS_FIELD is None:
        STORY_POINTS_FIELD = client.get_story_points_field()
    return STORY_POINTS_FIELD


def utc_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000+00:00")


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def transition_to(issue_key: str, status_name: str) -> bool:
    try:
        result = client._get(f"/rest/api/3/issue/{issue_key}/transitions")
        for t in result.get("transitions", []):
            if t["to"]["name"].lower() == status_name.lower():
                client._post(
                    f"/rest/api/3/issue/{issue_key}/transitions",
                    {"transition": {"id": t["id"]}},
                )
                return True
    except Exception as e:
        console.print(f"    [dim]transition {issue_key} → {status_name}: {e}[/dim]")
    return False


def create_project_if_missing(key: str, name: str) -> bool:
    try:
        client.get_project(key)
        console.print(f"  [yellow]~[/yellow] Project {key} already exists")
        return True
    except Exception:
        pass
    try:
        payload = {
            "key": key,
            "name": name,
            "projectTypeKey": "software",
            "projectTemplateKey": "com.pyxis.greenhopper.jira:gh-scrum-template",
            "leadAccountId": ADMIN_ACCOUNT_ID,
        }
        client._post("/rest/api/3/project", payload)
        console.print(f"  [green]✓[/green] Created project {key} — {name}")
        time.sleep(SLEEP)
        return True
    except Exception as e:
        console.print(f"  [red]✗[/red] Failed to create {key}: {e}")
        return False


# ── Step 1: Verify connection ──────────────────────────────────────────────────

def step_verify():
    console.rule("[bold blue]Step 1: Verify Jira Cloud connection")
    me = client.get_myself()
    console.print(f"  [green]✓[/green] Connected as [bold]{me.get('displayName')}[/bold] ({me.get('emailAddress')})")
    return me


# ── Step 2: Ensure projects exist ─────────────────────────────────────────────

def step_projects() -> list[str]:
    console.rule("[bold blue]Step 2: Projects")
    keys = [EXISTING_PROJECT_KEY]
    try:
        proj = client.get_project(EXISTING_PROJECT_KEY)
        console.print(f"  [green]✓[/green] Project {EXISTING_PROJECT_KEY} ({proj['name']}) already exists")
    except Exception as e:
        console.print(f"  [red]✗[/red] Cannot access {EXISTING_PROJECT_KEY}: {e}")

    for p in PROJECTS_TO_CREATE:
        if create_project_if_missing(p["key"], p["name"]):
            keys.append(p["key"])

    return keys


# ── Step 3: Create epics ───────────────────────────────────────────────────────

def step_epics(project_keys: list[str]) -> dict[str, list[str]]:
    console.rule("[bold blue]Step 3: Epics")
    epic_keys: dict[str, list[str]] = {}

    for proj_key in project_keys:
        epic_keys[proj_key] = []
        names = EPICS_BY_PROJECT.get(proj_key, [])
        for name in names:
            try:
                result = client.create_issue(
                    project_key=proj_key,
                    summary=name,
                    issue_type="Epic",
                    description=f"Epic: {name}",
                )
                key = result["key"]
                epic_keys[proj_key].append(key)
                console.print(f"  [green]✓[/green] {key} Epic: {name}")
                time.sleep(SLEEP)
            except Exception as e:
                console.print(f"  [red]✗[/red] Epic '{name}' in {proj_key}: {e}")
        console.print(f"  → {len(epic_keys[proj_key])} epics in {proj_key}")

    return epic_keys


# ── Step 4: Create stories ─────────────────────────────────────────────────────

def step_stories(project_keys: list[str], epic_keys: dict) -> dict[str, list[str]]:
    console.rule("[bold blue]Step 4: Stories")
    story_keys: dict[str, list[str]] = {}
    sp = sp_field()

    for proj_key in project_keys:
        story_keys[proj_key] = []
        stories = STORIES_BY_PROJECT.get(proj_key, [])
        epics = epic_keys.get(proj_key, [])

        for summary, pts in stories:
            try:
                payload: dict = {
                    "project": {"key": proj_key},
                    "summary": summary,
                    "issuetype": {"name": "Story"},
                }
                result = client._post("/rest/api/3/issue", {"fields": payload})
                key = result["key"]
                story_keys[proj_key].append(key)
                # Set story points via update (avoids field-scheme 400 on creation)
                try:
                    client._put(f"/rest/api/3/issue/{key}", {"fields": {sp: pts}})
                except Exception:
                    pass
                # Set timetracking (1 SP = 1 hour)
                try:
                    client._put(f"/rest/api/3/issue/{key}", {
                        "fields": {
                            "timetracking": {
                                "originalEstimate": f"{pts}h",
                                "remainingEstimate": f"{pts}h",
                            }
                        }
                    })
                except Exception as e:
                    console.print(f"    [dim]timetracking {key}: {e}[/dim]")
                console.print(f"  [green]✓[/green] {key} ({pts}pts)")
                time.sleep(SLEEP)
            except Exception as e:
                console.print(f"  [red]✗[/red] Story '{summary}' in {proj_key}: {e}")

        console.print(f"  → {len(story_keys[proj_key])} stories in {proj_key}")

    return story_keys


# ── Step 5: Create bugs ────────────────────────────────────────────────────────

def step_bugs(project_keys: list[str]) -> dict[str, list[str]]:
    console.rule("[bold blue]Step 5: Bugs")
    bug_keys: dict[str, list[str]] = {}

    for proj_key in project_keys:
        bug_keys[proj_key] = []
        bugs = BUGS_BY_PROJECT.get(proj_key, [])

        for summary, priority in bugs:
            try:
                result = client.create_issue(
                    project_key=proj_key,
                    summary=summary,
                    issue_type="Bug",
                    priority=priority,
                )
                key = result["key"]
                bug_keys[proj_key].append(key)
                bug_hours = "4h" if priority in ("Highest", "High") else "2h"
                try:
                    client._put(f"/rest/api/3/issue/{key}", {
                        "fields": {
                            "timetracking": {
                                "originalEstimate": bug_hours,
                                "remainingEstimate": bug_hours,
                            }
                        }
                    })
                except Exception as e:
                    console.print(f"    [dim]timetracking {key}: {e}[/dim]")
                console.print(f"  [green]✓[/green] {key} [{priority}] {summary}")
                time.sleep(SLEEP)
            except Exception as e:
                console.print(f"  [red]✗[/red] Bug '{summary}' in {proj_key}: {e}")

        console.print(f"  → {len(bug_keys[proj_key])} bugs in {proj_key}")

    return bug_keys


# ── Step 6: Create tasks ───────────────────────────────────────────────────────

def step_tasks(project_keys: list[str]) -> dict[str, list[str]]:
    console.rule("[bold blue]Step 6: Tasks")
    task_keys: dict[str, list[str]] = {}
    sp = sp_field()

    for proj_key in project_keys:
        task_keys[proj_key] = {}
        tasks = TASKS_BY_PROJECT.get(proj_key, [])
        keys = []

        for summary, pts in tasks:
            try:
                payload = {
                    "project": {"key": proj_key},
                    "summary": summary,
                    "issuetype": {"name": "Task"},
                }
                result = client._post("/rest/api/3/issue", {"fields": payload})
                key = result["key"]
                keys.append(key)
                try:
                    client._put(f"/rest/api/3/issue/{key}", {"fields": {sp: pts}})
                except Exception:
                    pass
                # Set timetracking (1 SP = 1 hour)
                try:
                    client._put(f"/rest/api/3/issue/{key}", {
                        "fields": {
                            "timetracking": {
                                "originalEstimate": f"{pts}h",
                                "remainingEstimate": f"{pts}h",
                            }
                        }
                    })
                except Exception as e:
                    console.print(f"    [dim]timetracking {key}: {e}[/dim]")
                console.print(f"  [green]✓[/green] {key} {summary}")
                time.sleep(SLEEP)
            except Exception as e:
                console.print(f"  [red]✗[/red] Task '{summary}' in {proj_key}: {e}")

        task_keys[proj_key] = keys
        console.print(f"  → {len(keys)} tasks in {proj_key}")

    return task_keys


# ── Step 7: Sprints ────────────────────────────────────────────────────────────

SPRINT_CONFIG = [
    {"name": "Sprint 1", "weeks_ago": 10, "duration": 2, "assign": 10, "done": 8,  "state": "closed"},
    {"name": "Sprint 2", "weeks_ago": 8,  "duration": 2, "assign": 12, "done": 9,  "state": "closed"},
    {"name": "Sprint 3", "weeks_ago": 6,  "duration": 2, "assign": 10, "done": 7,  "state": "closed"},
    {
        "name": "Sprint 4 - Current",
        "weeks_ago": 0, "duration": 2,
        "assign": 20,
        "state": "active",
        "distribution": {
            "Done": 5,
            "In Progress": 8,
            "In Review": 4,
            "To Do": 3,
        },
    },
]

# INF is Kanban — only SCRUM and CRM get sprints
SCRUM_PROJECTS = ["SCRUM", "CRM"]

SEED_SPRINT_MARKERS = ("Sprint 1", "Sprint 2", "Sprint 3", "Sprint 4")


def step_cleanup_sprints() -> None:
    console.rule("[bold blue]Step 0: Cleanup old seed sprints (future only)")
    deleted = 0
    for proj_key in SCRUM_PROJECTS:
        boards = client.get_boards(proj_key)
        for board in boards:
            board_id = board["id"]
            try:
                sprints = client.get_sprints(board_id)
            except Exception as e:
                console.print(f"  [dim]Board {board_id} sprints: {e}[/dim]")
                continue
            for s in sprints:
                if s["state"] != "future":
                    continue
                if not any(m in s["name"] for m in SEED_SPRINT_MARKERS):
                    continue
                try:
                    url = f"{client.base_url}/rest/agile/1.0/sprint/{s['id']}"
                    r = httpx.delete(
                        url, auth=client.auth, headers=client.headers, timeout=30
                    )
                    if r.is_success:
                        console.print(f"  [yellow]~[/yellow] Deleted future sprint: {s['name']}")
                        deleted += 1
                    else:
                        console.print(f"  [dim]Cannot delete {s['name']}: HTTP {r.status_code}[/dim]")
                except Exception as e:
                    console.print(f"  [dim]Delete {s['name']}: {e}[/dim]")
                time.sleep(SLEEP)
    if deleted == 0:
        console.print("  [dim]No future seed sprints found to delete[/dim]")
    else:
        console.print(f"  → {deleted} sprint(s) deleted")


def step_sprints(story_keys: dict, bug_keys: dict, task_keys: dict) -> dict:
    console.rule("[bold blue]Step 7: Sprints")
    sprint_summary: dict = {}

    for proj_key in SCRUM_PROJECTS:
        boards = client.get_boards(proj_key)
        if not boards:
            console.print(f"  [red]No board for {proj_key}[/red]")
            continue

        board_id = boards[0]["id"]
        console.print(f"  Board {board_id} for {proj_key}")

        # Pool of issues to assign to sprints
        pool = (
            story_keys.get(proj_key, [])
            + bug_keys.get(proj_key, [])
            + task_keys.get(proj_key, [])
        )
        random.shuffle(pool)
        sprint_summary[proj_key] = []
        cursor = 0

        for cfg in SPRINT_CONFIG:
            now = now_utc()
            start = now - timedelta(weeks=cfg["weeks_ago"] + cfg["duration"])
            end = start + timedelta(weeks=cfg["duration"])

            try:
                sprint = client.create_sprint(
                    board_id=board_id,
                    name=f"{proj_key} {cfg['name']}",
                    start_date=utc_iso(start),
                    end_date=utc_iso(end),
                )
                sprint_id = sprint["id"]
                time.sleep(SLEEP)

                # Assign issues
                assign_count = cfg["assign"]
                chunk = pool[cursor: cursor + assign_count]
                cursor += assign_count

                if chunk:
                    client.move_issues_to_sprint(sprint_id, chunk)
                    time.sleep(SLEEP)

                sprint_name = f"{proj_key} {cfg['name']}"

                if cfg["state"] == "closed":
                    # Start sprint first
                    client.update_sprint(sprint_id, {
                        "name": sprint_name,
                        "state": "active",
                        "startDate": utc_iso(start),
                        "endDate": utc_iso(end),
                    })
                    time.sleep(SLEEP)

                    done_count = cfg["done"]
                    for key in chunk[:done_count]:
                        transition_to(key, "Done")
                        time.sleep(0.2)

                    # Close sprint
                    client.update_sprint(sprint_id, {
                        "name": sprint_name,
                        "state": "closed",
                        "startDate": utc_iso(start),
                        "endDate": utc_iso(end),
                        "completeDate": utc_iso(end),
                    })
                    time.sleep(SLEEP)
                    console.print(
                        f"  [green]✓[/green] {cfg['name']} (closed) — "
                        f"{len(chunk)} issues, {done_count} done"
                    )
                    sprint_summary[proj_key].append({"name": cfg["name"], "state": "closed", "done": done_count})

                else:  # active
                    active_start = now - timedelta(days=1)
                    active_end = now + timedelta(days=13)
                    client.update_sprint(sprint_id, {
                        "name": sprint_name,
                        "state": "active",
                        "startDate": utc_iso(active_start),
                        "endDate": utc_iso(active_end),
                    })
                    time.sleep(SLEEP)

                    dist = cfg.get("distribution", {})
                    issue_list = list(chunk)
                    idx = 0
                    for status, count in dist.items():
                        if status == "To Do":
                            idx += count
                            continue
                        for key in issue_list[idx: idx + count]:
                            transition_to(key, status)
                            time.sleep(0.2)
                        idx += count

                    console.print(
                        f"  [green]✓[/green] {cfg['name']} (active) — "
                        f"{len(chunk)} issues, mixed states"
                    )
                    sprint_summary[proj_key].append({"name": cfg["name"], "state": "active"})

            except Exception as e:
                console.print(f"  [red]✗[/red] Sprint '{cfg['name']}' in {proj_key}: {e}")

    return sprint_summary


# ── Summary ────────────────────────────────────────────────────────────────────

def print_summary(
    project_keys: list[str],
    epic_keys: dict,
    story_keys: dict,
    bug_keys: dict,
    task_keys: dict,
    sprint_summary: dict,
) -> None:
    console.rule("[bold green]SEED COMPLETE")

    total_issues = sum(
        len(epic_keys.get(k, [])) +
        len(story_keys.get(k, [])) +
        len(bug_keys.get(k, [])) +
        len(task_keys.get(k, []))
        for k in project_keys
    )
    total_sprints = sum(len(v) for v in sprint_summary.values())
    closed_sprints = sum(
        sum(1 for s in v if s["state"] == "closed")
        for v in sprint_summary.values()
    )
    active_sprints = total_sprints - closed_sprints

    table = Table(title="Seed Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="magenta")
    table.add_row("Projects", str(len(project_keys)))
    table.add_row("Total issues created", str(total_issues))
    table.add_row("Sprints total", str(total_sprints))
    table.add_row("  Closed", str(closed_sprints))
    table.add_row("  Active", str(active_sprints))
    console.print(table)
    console.print("\n[bold green]Dashboards:[/bold green] http://localhost:8000/dashboard/overview")


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    step_verify()
    step_cleanup_sprints()
    project_keys = step_projects()
    epic_keys = step_epics(project_keys)
    story_keys = step_stories(project_keys, epic_keys)
    bug_keys = step_bugs(project_keys)
    task_keys = step_tasks(project_keys)
    sprint_summary = step_sprints(story_keys, bug_keys, task_keys)
    print_summary(project_keys, epic_keys, story_keys, bug_keys, task_keys, sprint_summary)
