# Jira Dashboard — Local Dev Environment

100% local Docker setup: Jira Software + FastAPI dashboards + simulated project data.

## Stack

| Service  | Image / Tech              | Port  |
|----------|---------------------------|-------|
| postgres | postgres:14               | 5432  |
| jira     | atlassian/jira-software   | 8080  |
| api      | Python 3.12 / FastAPI     | 8000  |

## Prerequisites

- Docker Desktop with ≥4 GB RAM allocated
- Docker Compose v2

## Quick Start

```bash
# 1. Enter project directory
cd jira-dashboard

# 2. Create env file
cp .env.example .env

# 3. Start Jira + Postgres (takes 2–4 min first boot)
docker compose up postgres jira -d

# 4. Watch logs until Jira is ready
docker compose logs -f jira
# Wait for: "Jira is ready to serve requests"

# 5. Open http://localhost:8080 and complete the setup wizard
#    - Choose "Set it up for me" (evaluation license, 30 days)
#    - Create admin user: admin / admin_password  (or your own)
#    - Update .env with the credentials you chose

# 6. Start the API
docker compose up api -d

# 7. Seed realistic data
docker compose exec api python seed/seed_data.py

# 8. Open dashboards
open http://localhost:8000/dashboard/overview
```

## Dashboards

| URL                            | Description                        |
|--------------------------------|------------------------------------|
| `/dashboard/overview`          | KPIs across all projects           |
| `/dashboard/velocity`          | Sprint velocity (committed vs done)|
| `/dashboard/burndown`          | Active sprint burndown chart       |
| `/dashboard/backlog`           | Backlog health by type/priority    |
| `/dashboard/team`              | Workload per team member           |

## JSON API

| Endpoint               | Description                    |
|------------------------|--------------------------------|
| `GET /api/overview`    | Global KPIs                    |
| `GET /api/velocity/{project}` | Velocity data          |
| `GET /api/burndown/{project}` | Burndown data          |
| `GET /api/backlog/{project}`  | Backlog distribution   |
| `GET /api/team/{project}`     | Team workload          |

API docs: http://localhost:8000/docs

## Simulated Data (per project)

- **3 Projects**: MDA (Scrum), CRM (Scrum), INF (Kanban)
- **8 Users**: Frontend, Backend, QA, Designer, SM, PO, DevOps
- **Per project**: 5 Epics · 30 Stories · 15 Bugs · 10 Tasks
- **Sprints**: 3 closed + 1 active + 1 future (Scrum projects)
- **Workflow**: To Do → In Progress → In Review → Done / Blocked

## Apple Silicon Notes

The `docker-compose.yml` sets `platform: linux/amd64` on the Jira service.
Rosetta emulation handles this automatically on M1/M2/M3 Macs.

## Memory

Jira needs ≥4 GB RAM in Docker Desktop preferences.
Reduce `JVM_MAXIMUM_MEMORY` to `1536m` in `docker-compose.yml` if constrained.

## Reset

```bash
# Wipe all data and start fresh
docker compose down -v
docker compose up postgres jira -d
```
