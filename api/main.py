from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from routers import overview, velocity, burndown, backlog, team, sprint_dashboard

app = FastAPI(title="Jira Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router)
app.include_router(velocity.router)
app.include_router(burndown.router)
app.include_router(backlog.router)
app.include_router(team.router)
app.include_router(sprint_dashboard.router)


@app.get("/")
def root():
    return RedirectResponse(url="/health")


@app.get("/health")
def health():
    return {"status": "ok", "service": "jira-dashboard-api"}


@app.get("/api/projects")
def api_projects():
    from jira_client import JiraClient
    client = JiraClient()
    projects = client.get_all_projects()
    return [{"key": p["key"], "name": p["name"]} for p in projects]


@app.get("/test-jira")
def test_jira():
    from jira_client import JiraClient
    client = JiraClient()
    me = client.get_myself()
    projects = client.get_all_projects()
    return {
        "connected_as": me.get("displayName"),
        "account_id": me.get("accountId"),
        "email": me.get("emailAddress"),
        "projects": [{"key": p["key"], "name": p["name"]} for p in projects],
    }
