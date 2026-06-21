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

## JSON API

| Endpoint                              | Description                    |
|---------------------------------------|--------------------------------|
| `GET /api/overview`                   | Global KPIs                    |
| `GET /api/velocity/{project}`         | Velocity data                  |
| `GET /api/burndown/{project}`         | Burndown data                  |
| `GET /api/backlog/{project}`          | Backlog distribution           |
| `GET /api/team/{project}`             | Team workload                  |
| `GET /api/sprint-dashboard/data`      | Sprint dashboard (board+sprint)|

API docs: http://localhost:8000/docs

## Running Tests

```bash
cd api
python3 -m pytest tests/ -v
```
