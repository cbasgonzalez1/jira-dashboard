# Jira Dashboard

FastAPI + React dashboard that connects directly to Jira Server via REST API.

## Stack

| Service  | Tech                      | Port  |
|----------|---------------------------|-------|
| api      | Python 3.12 / FastAPI     | 8000  |
| frontend | React / Vite / Tailwind   | 5173  |

## Prerequisites

- Python 3.12+
- Node.js 18+
- Access to a Jira Server instance

## Quick Start

```bash
# 1. Enter project directory
cd jira-dashboard

# 2. Create env file and fill in your credentials
cp .env.example .env

# 3. Install API dependencies
cd api && pip install -r requirements.txt

# 4. Start the API
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 5. In a second terminal, install and start the frontend
cd frontend && npm install && npm run dev
```

## Configuration (.env)

| Variable                 | Default | Description                                      |
|--------------------------|---------|--------------------------------------------------|
| `JIRA_BASE_URL`          | —       | Base URL of your Jira Server (required)          |
| `JIRA_USER`              | —       | Jira username (required)                         |
| `JIRA_PASSWORD`          | —       | Jira password (required)                         |
| `WORK_HOURS_PER_DAY`     | 8       | Working hours per day for capacity calculation   |
| `TEAM_UTILIZATION_FACTOR`| 0.8     | Team utilization factor (0–1) for capacity calc  |
| `VELOCITY_SPRINT_WINDOW` | 3       | Number of past closed sprints for velocity avg   |

## Dashboards

| URL                            | Description                        |
|--------------------------------|------------------------------------|
| `/dashboard/overview`          | KPIs across all projects           |
| `/dashboard/velocity`          | Sprint velocity (committed vs done)|
| `/dashboard/burndown`          | Active sprint burndown chart       |
| `/dashboard/backlog`           | Backlog health by type/priority    |
| `/dashboard/team`              | Workload per team member           |

Most teams in this Jira instance estimate and log work in **hours**
(`timetracking`), not story points, so Velocity and Burndown use hours as
the primary metric — story points are shown alongside as a secondary value
only when a project actually has them loaded.

- **Velocity / Burndown**: since several boards in this instance are shared
  across multiple projects, both pages let you pick a specific
  Tablero (board) → Sprint instead of guessing. Sprint/velocity totals are
  always filtered down to the selected project's own issues, even when the
  underlying sprint spans other projects too.
- **Carga de equipo (Team)**: toggle between **Sprint actual** (issues in
  the project's currently active sprint(s)) and **Backlog total** (all
  unresolved issues) — a person's numbers can look very different between
  the two, so both are available rather than only one.

## JSON API

| Endpoint                                          | Description                                   |
|----------------------------------------------------|-----------------------------------------------|
| `GET /api/overview`                                 | Global KPIs                                    |
| `GET /api/velocity/{project}?board_id=`             | Velocity data (hours primary, points secondary)|
| `GET /api/burndown/{project}?board_id=&sprint_id=`  | Burndown data (hours primary, points secondary)|
| `GET /api/backlog/{project}`                        | Backlog distribution                           |
| `GET /api/team/{project}`                           | Team workload — `{sprint, backlog}` per person |
| `GET /api/sprint-dashboard/data`                    | Sprint dashboard (board+sprint)                |

`board_id`/`sprint_id` are optional; when omitted the API falls back to the
project's first board and its active sprint.

API docs: http://localhost:8000/docs

## Running Tests

```bash
cd api
python3 -m pytest tests/ -v
```
