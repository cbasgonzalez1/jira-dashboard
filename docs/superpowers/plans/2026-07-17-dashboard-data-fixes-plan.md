# Plan de implementación: Reparación de datos (Resumen, Velocidad, Burndown, Equipo)

**Spec:** `docs/superpowers/specs/2026-07-17-dashboard-data-fixes-design.md`
**Fecha:** 2026-07-17

Cada fase deja el repo en estado funcional (tests en verde) antes de pasar a la siguiente. Comando de referencia para verificar en cada checkpoint:

```bash
cd api && python3 -m pytest tests/ -v
```

---

## Fase 1 — `status_category.py` (módulo nuevo)

**Archivo:** `api/status_category.py`

- `categorize(status_field: dict) -> str` — lee `status_field.get("statusCategory", {}).get("key")`, mapea `"new"→"todo"`, `"indeterminate"→"in_progress"`, `"done"→"done"`; si falta o es desconocido, devuelve `"in_progress"`.

**Tests:** `api/tests/test_status_category.py` — casos con los `statusCategory.key` reales (`new`, `indeterminate`, `done`), clave desconocida, y diccionario vacío/ausente.

**Checkpoint:** `pytest tests/test_status_category.py -v` en verde.

---

## Fase 2 — `effort.py` (módulo nuevo)

**Archivo:** `api/effort.py`

- `extract_effort(fields: dict, sp_field: str) -> dict` con `committed_h`, `done_h`, `committed_sp`, `done_sp`.
  - Horas: `timetracking.originalEstimateSeconds` o `timeoriginalestimate` → `committed_h` (÷3600); `timetracking.timeSpentSeconds` o `timespent` → `done_h` (÷3600). `done_h` solo se usa cuando el issue está en categoría "done" (el caller decide, esta función solo extrae los números crudos).
  - Puntos: `fields.get(sp_field) or fields.get("customfield_11934") or 0` → `committed_sp`; el caller decide si cuenta como `done_sp` según su propia categorización.
  - Nota de diseño: esta función es un extractor puro (no decide done/no-done); mantiene la responsabilidad de clasificar en `status_category.py`, evitando lógica duplicada.

**Tests:** `api/tests/test_effort.py` — con horas, con story points, sin ninguno, con ambos.

**Checkpoint:** `pytest tests/test_effort.py -v` en verde.

---

## Fase 3 — `conftest.py`: soporte para `statusCategory` en fixtures

**Archivo:** `api/tests/conftest.py`

- `make_issue()` agrega parámetro `category: str | None = None`. Si no se pasa, se infiere del `status` recibido con una tabla de mapeo local del propio conftest (para no romper ~30 tests existentes que solo pasan `status="Done"`, `"In Progress"`, `"To Do"`, `"Blocked"`).
- Se agrega el bloque `"statusCategory": {"key": category}` dentro de `fields.status`.

**Checkpoint:** `pytest tests/ -v` — la suite completa debe seguir en verde (fixtures nuevas no deben romper tests existentes porque `status_category.py` aún no se usa en los routers).

---

## Fase 4 — `overview.py`

**Archivo:** `api/routers/overview.py`

- `_fetch_project_data()`: JQL de `epics_ip` cambia de `status = "In Progress"` a `statusCategory = "In Progress"`.
- `sprint_done` se calcula con `status_category.categorize(i["fields"]["status"]) == "done"` en vez de comparar contra `DONE_STATUSES`.
- Quita el import de `constants` si ya no se usa nada más de él en este archivo.

**Tests:** actualizar `test_overview.py` — el test de `epics_in_progress` debe reflejar el nuevo JQL (mockeado) y `sprint_done` debe cubrir un status no incluido en el viejo `DONE_STATUSES` (p. ej. `"Listo"`) para probar que ahora sí se cuenta.

**Checkpoint:** `pytest tests/test_overview.py -v` en verde.

---

## Fase 5 — `velocity.py`

**Archivo:** `api/routers/velocity.py`

- `get_velocity_data(project_key, board_id: int | None = None)`:
  - Si se pasa `board_id`, se usa directo (validando que pertenezca al proyecto vía `client.get_boards(project_key)`; si no pertenece, falla igual que "sin boards").
  - Si no se pasa, intenta un tablero cuya `location.projectKey` (de `client.get_board_configuration(board_id)` o el campo `location` del board) coincida exactamente con `project_key`; si ninguno coincide, cae a `boards[0]` (comportamiento actual, como red de seguridad).
- Por cada sprint: usa `effort.extract_effort()` y `status_category.categorize()` para calcular `committed_h`/`done_h` (principal) y `committed_sp`/`done_sp` (secundario, solo si no son 0).
- `avg_velocity` se recalcula en horas (`avg_velocity_h`); se mantiene `avg_velocity` como alias del valor en horas para no romper el contrato existente del frontend en el primer commit, y se agrega `avg_velocity_sp` si aplica.
- Endpoint `/api/velocity/{project}` y `/dashboard/velocity` aceptan `board_id: int | None = Query(None)`.

**Tests:** actualizar `test_velocity.py` para horas como base (usando `orig_s`/`spent_s` de `make_issue`), agregar test de `board_id` explícito y de fallback por `location.projectKey`.

**Checkpoint:** `pytest tests/test_velocity.py -v` en verde.

---

## Fase 6 — `burndown.py`

**Archivo:** `api/routers/burndown.py`

- `get_burndown_data(project_key, board_id: int | None = None, sprint_id: int | None = None)`:
  - Mismo criterio de selección de tablero que velocity.py.
  - Si se pasa `sprint_id`, se busca ese sprint específico entre los sprints del tablero (activos o cerrados) en vez de asumir "el primer sprint activo".
- `total_pts`/`done_pts` pasan a ser `total_h`/`done_h` (principal); se agregan `total_sp`/`done_sp` como datos secundarios cuando no son 0. Se mantienen `total_pts`/`done_pts`/`remaining_pts` como alias de los valores en horas por compatibilidad con el contrato JSON actual del primer commit.
- `ideal`/`actual` se calculan sobre horas.
- Endpoint acepta `board_id`, `sprint_id` opcionales.

**Tests:** actualizar `test_burndown.py` para horas, agregar test de `sprint_id` explícito.

**Checkpoint:** `pytest tests/test_burndown.py -v` en verde.

---

## Fase 7 — `team.py`

**Archivo:** `api/routers/team.py`

- `get_team_data(project_key)` calcula dos agregados por usuario en vez de uno:
  - `backlog`: comportamiento actual (todos los issues sin resolver del proyecto) — se reutiliza la consulta ya existente.
  - `sprint`: se obtienen todos los tableros del proyecto (`client.get_boards`), todos sus sprints activos (`client.get_sprints(board_id, state="active")`), se listan los issues de esos sprints (`client.get_sprint_issues`) y se agregan de la misma forma que `backlog`, pero filtrando a este proyecto (por si el tablero es compartido entre proyectos — usar el filtro `project = {key}` no aplica aquí porque los issues ya vienen del sprint; hay que filtrar por `fields.project.key == project_key` para excluir issues de otros proyectos en tableros compartidos).
  - `by_type`/`blocked`/`issues`/`story_points` (u horas, ver nota abajo) se calculan igual en ambos bloques.
- Nota de unidades: `team.py` hoy suma `story_points`; dado que casi nadie los usa, se cambia a sumar también horas comprometidas (`effort.extract_effort()`) y se expone `hours` junto a `story_points` en cada bloque, sin quitar `story_points` (compatibilidad).
- Forma de retorno: `{"project": ..., "users": [[username, {"display":..., "backlog": {...}, "sprint": {...}}], ...], "total_issues": ...}`.

**Tests:** actualizar `test_team.py` para la forma anidada `backlog`/`sprint`, agregar test de filtrado por proyecto en tableros compartidos.

**Checkpoint:** `pytest tests/test_team.py -v` en verde.

---

## Fase 8 — `sprint_dashboard.py`

**Archivo:** `api/routers/sprint_dashboard.py`

- Reemplaza `_cat()`/`_STATUS_MAP` por `status_category.categorize()`.
- Reemplaza `_sp()` por `effort.extract_effort()` (mantiene su forma de uso actual: `committed_sp` en vez de `_sp()`).
- Quita el import de `constants`.

**Tests:** `pytest tests/test_sprint_dashboard.py -v` — no debería requerir cambios grandes porque el contrato de salida no cambia, solo la clasificación interna; agregar un caso con status `"Listo"`/`"Resuelta"` para confirmar que ahora se cuenta como `done`.

**Checkpoint:** `pytest tests/test_sprint_dashboard.py -v` en verde.

---

## Fase 9 — `constants.py`

- Una vez que ningún router importa `DONE_STATUSES`/`TODO_STATUSES`/`IN_PROGRESS_STATUSES` (verificar con `grep -rn "from constants" api/routers`), se elimina el archivo.

**Checkpoint:** `pytest tests/ -v` — suite completa en verde, sin imports rotos.

---

## Fase 10 — Templates Jinja (`api/templates/`)

Los dashboards HTML nativos (`/dashboard/velocity`, `/dashboard/burndown`, `/dashboard/team`) siguen sirviendo el mismo contexto que ahora devuelven los routers, así que:

- `velocity.html` / `burndown.html`: cambiar las etiquetas "Story Points" / "pts" por "Horas" / "h", usando los nuevos campos `*_h`. Sin selector de tablero/sprint en esta vista (se puede pasar `?board_id=`/`&sprint_id=` por URL como mejora futura, fuera de alcance).
- `team.html`: mostrar el bloque `backlog` por persona (comportamiento equivalente al actual); agregar una nota/sección aparte para `sprint` sin necesitar JS interactivo (dos tablas o dos columnas).

**Checkpoint:** levantar el servidor localmente y visitar `/dashboard/velocity?project=AIC`, `/dashboard/burndown?project=AIC`, `/dashboard/team?project=AIC` — confirmar que no hay errores 500 y que los números ya no están en 0 para un sprint con datos reales.

---

## Fase 11 — Frontend

**Archivos:** `frontend/src/api/jiraApi.js`, `frontend/src/pages/Velocity.jsx`, `frontend/src/pages/Burndown.jsx`, `frontend/src/pages/TeamLoad.jsx`

- `jiraApi.js`: `getVelocity(project, boardId)` y `getBurndown(project, boardId, sprintId)` agregan los params opcionales a la query string.
- `Velocity.jsx` / `Burndown.jsx`: agregan selector Tablero → Sprint reutilizando `getSprintBoards`/`getSprintSprints` (ya existentes, usados hoy por `SprintDashboard.jsx`) y el componente `Select` (extraer de `SprintDashboard.jsx` a `components/ui/Select.jsx` para reutilizarlo en las tres páginas en vez de duplicarlo).
- Los KPI y textos de "pts"/"Story Points" pasan a "h"/"Horas" como unidad principal; si `*_sp` viene con datos, se muestra como subtítulo secundario en la tarjeta correspondiente.
- `TeamLoad.jsx`: agrega un toggle (dos botones o un `Select`) "Sprint actual" / "Backlog total" que cambia qué bloque (`data.users[i][1].sprint` vs `.backlog`) alimenta las tarjetas y el gráfico de barras. Por defecto abre en "Sprint actual".

**Checkpoint:** `npm run dev` en `frontend/`, navegar manualmente los tres dashboards con un proyecto real (AIC) y confirmar visualmente que los números cambian según el sprint/tablero seleccionado y ya no aparecen en 0.

---

## Fase 12 — Verificación final end-to-end

- Suite completa: `cd api && python3 -m pytest tests/ -v` en verde.
- Smoke test manual contra Jira real (ya hay `.env` configurado) para 2-3 proyectos distintos, comparando antes/después:
  - `AIC` (tablero compartido "SW Ground MISC") — confirmar que con `board_id` explícito del tablero propio los datos ya no coinciden por casualidad con otros proyectos.
  - Un proyecto que solo usa horas (la mayoría) — confirmar que velocidad/burndown ya no muestran 0.
  - Confirmar en `team.py` que una persona con muchos issues de backlog histórico ya no se ve "anormal" en la vista "Sprint actual".
- Revisar que `.env` (con credenciales reales) no quede staged para commit (`git status` antes de cualquier commit final).

---

## Orden de commits sugerido

1. Fases 1-3 (helpers + fixtures) — un commit.
2. Fase 4 (overview) — un commit.
3. Fases 5-6 (velocity + burndown) — un commit (están acopladas por el mismo criterio de selección de tablero).
4. Fase 7 (team) — un commit.
5. Fase 8-9 (sprint_dashboard + limpieza de constants.py) — un commit.
6. Fase 10 (templates Jinja) — un commit.
7. Fase 11 (frontend) — uno o dos commits (selector reutilizable + páginas).

Cada commit deja `pytest tests/ -v` en verde.

---

## Fase 13 — Cierre (2026-07-18)

Verificación end-to-end contra Jira real destapó dos causas raíz adicionales no cubiertas por el diseño original, más un cabo suelto del frontend:

1. **`TeamBarChart.jsx` no se había tocado en la Fase 11** — su tooltip seguía mostrando `story_points` (0 para casi todos los equipos). Corregido para mostrar horas, igual que el resto del rediseño.
2. **Velocity/Burndown mezclaban datos de otros proyectos.** Los tableros de este Jira no tienen `location` (el endpoint de configuración no lo expone) y sus filtros son genuinamente cruzados entre proyectos (verificado leyendo el JQL real del filtro de cada tablero) — la estrategia de "matchear por location" del diseño original no era viable. Fix real: igual que ya hacía `team.py`, se filtran los issues del sprint por `fields.project.key == project_key` antes de sumar horas/puntos (`velocity.py::_sprint_effort`, `burndown.py`). Confirmado con datos reales: el committed de AIC bajó de 1084h (contaminado con THED/SATH/DEVOPSSP/...) a 64h (solo AIC), y da el mismo resultado sin importar cuál de los dos tableros compartidos se elija.
3. **El Resumen (`/api/overview`) estaba vacío para los 35 proyectos, siempre.** JQL de `critical_bugs` usaba `priority = Highest`, prioridad que no existe en este Jira (escala real: `Blocked > Crítica > High > Medium > Low`) — cada fetch por proyecto tiraba HTTP 400 y `overview.py` lo capturaba silenciosamente devolviendo `None` por proyecto, dejando el dashboard entero en cero. Además, filtrar por el nombre literal `"Crítica"` también falla en este servidor (probable problema de normalización Unicode en su parser JQL) — el fix usa los IDs de prioridad (`10402`=Blocked, `2`=Crítica) en vez del nombre.
4. **README actualizado** para documentar horas como métrica principal, selector Tablero→Sprint y el toggle Sprint actual/Backlog total.

Verificado contra Jira real (proyecto AIC): `/api/overview` pasa de todo en cero a 35 proyectos con datos (4420 issues abiertos, 30 bugs críticos, 40 épicas en curso); `/api/velocity/AIC` y `/api/burndown/AIC` devuelven horas correctas y consistentes entre los dos tableros compartidos; `/api/team/AIC` y `/api/sprint-dashboard/data` devuelven datos coherentes. Suite completa (`pytest tests/ -v`) sigue en 65/65 verde.

No se pudo tomar captura de pantalla del frontend: este contenedor no tiene navegador headless disponible (`chromium-cli` no está instalado, `npx playwright install --with-deps` requiere `sudo` interactivo no disponible aquí). La verificación de UI se hizo por inspección de código (los componentes consumen exactamente los campos que la API devuelve) más pruebas directas de la API real, no por captura visual.
