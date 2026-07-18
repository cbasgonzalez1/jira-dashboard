# Plan de implementación: alcance real por tablero y eliminación de demo data

**Spec:** `docs/superpowers/specs/2026-07-18-board-scoped-data-integrity-design.md`
**Fecha:** 2026-07-18

Cada fase deja el repo en estado funcional (tests en verde) antes de pasar a la siguiente.

```bash
cd api && python3 -m pytest tests/ -v
```

---

## Fase 1 — `jira_client.py`: `get_board_sprint_issues`

- Nuevo método `get_board_sprint_issues(self, board_id: int, sprint_id: int) -> list`, paginado sobre `GET /rest/agile/1.0/board/{board_id}/sprint/{sprint_id}/issue`, mismos `fields` por default que `get_sprint_issues_by_jql`.
- No se tocan `get_sprint_issues`/`get_sprint_issues_by_jql`.

**Checkpoint:** import y llamada manual contra Jira real (ya verificado en la investigación).

---

## Fase 2 — `velocity.py` y `burndown.py`

- `velocity.py::get_velocity_data`: dentro del loop de sprints, `client.get_sprint_issues(sprint["id"])` → `client.get_board_sprint_issues(selected_board_id, sprint["id"])`.
- `burndown.py::get_burndown_data`: `client.get_sprint_issues(selected_sprint_id)` → `client.get_board_sprint_issues(selected_board_id, selected_sprint_id)`.
- El filtro por `project.key` que ya tienen ambos se mantiene sin cambios.

**Tests:** actualizar mocks en `test_velocity.py`/`test_burndown.py` de `get_sprint_issues` a `get_board_sprint_issues`, verificando los argumentos `(board_id, sprint_id)`.

**Checkpoint:** `pytest tests/test_velocity.py tests/test_burndown.py -v` en verde.

---

## Fase 3 — `team.py`

- `_active_sprint_issues`: `client.get_sprint_issues(sprint["id"])` → `client.get_board_sprint_issues(board["id"], sprint["id"])`.

**Tests:** actualizar mocks en `test_team.py`.

**Checkpoint:** `pytest tests/test_team.py -v` en verde.

---

## Fase 4 — `sprint_dashboard.py`

- `dashboard_data`: `client.get_sprint_issues_by_jql(sprint_id)` → `client.get_board_sprint_issues(board_id, sprint_id)`.

**Tests:** actualizar mocks en `test_sprint_dashboard.py`.

**Checkpoint:** `pytest tests/test_sprint_dashboard.py -v` en verde.

---

## Fase 5 — `backlog.py`

- Agregar `timetracking`/`timespent`/`timeoriginalestimate` a los `fields` pedidos.
- `unestimated`: `not f.get(sp_field)` → `not f.get(sp_field) and extract_effort(f, sp_field)["committed_h"] == 0`.

**Tests:** nuevo caso en `test_backlog.py` — issue con horas pero sin story points no cuenta como sin estimar.

**Checkpoint:** `pytest tests/test_backlog.py -v` en verde.

---

## Fase 6 — Frontend: eliminar demo data y regex fake

- `SprintDashboard.jsx`: eliminar `DEMO_DATA` e `isDemo`; `displayData = data ?? null`; nuevo estado vacío para `!boardId || !sprintId`.
- `Velocity.jsx` (líneas 85, 133) y `VelocityChart.jsx` (línea 33): eliminar `.replace(/^(SCRUM|CRM|INF)\s/, '')`.

**Checkpoint:** sin referencias a `DEMO_DATA`/`SCRUM|CRM|INF` en el frontend (`grep`).

---

## Fase 7 — Verificación final end-to-end

- Suite completa `pytest tests/ -v` en verde.
- Smoke test contra Jira real: `DEVOPSSP` con los 3 tableros (5505/9333/5493) sobre el mismo sprint — confirmar que ahora dan números distintos (antes daban todos iguales).
- Capturas de las 4 pantallas afectadas (Velocity, Burndown, Team, Sprint Dashboard) si hay navegador headless disponible.
- Confirmar que no quedan menciones a `CRM`/`SCRUM`/`INF`/`SEC` fuera de `api/seed/` (que sigue sin usarse).

---

## Orden de commits sugerido

1. Fase 1 (cliente) + Fase 2 (velocity/burndown) — un commit, están acopladas.
2. Fase 3 (team) + Fase 4 (sprint_dashboard) — un commit.
3. Fase 5 (backlog) — un commit.
4. Fase 6 (frontend) — un commit.
