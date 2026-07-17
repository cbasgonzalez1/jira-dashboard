# Reparación de datos: Resumen, Velocidad, Burndown y Carga de equipo

**Fecha:** 2026-07-17
**Estado:** Aprobado para planificación

## Contexto

Los dashboards de Resumen, Velocidad, Burndown y Carga de equipo muestran datos incompletos: muchos valores en 0 y personas con cargas de trabajo fuera de lo normal. Se investigó contra la instancia real de Jira Server (`jira.aes.alcatel.fr`, 35 proyectos) para encontrar la causa raíz en lugar de adivinar.

## Causas raíz confirmadas

1. **Mapeo de estados "Done" incompleto y frágil.** `constants.py` compara el nombre literal del status (`"done"`, `"hecho"`, `"cerrado"`, `"resuelto"`, ...) contra `status.name` en minúsculas. La organización tiene más de 70 estados de workflow personalizados en 35 proyectos (`Listo`, `Resuelta`, `Cerrada`, `Cancelled`, `In Production`, `Test execution completed`, ...). Verificado en datos reales:
   - `"Listo"` — el estado de "terminado" más usado en el equipo probado (THED/AIC) — no está en `DONE_STATUSES`.
   - `"Resuelta"` (femenino) no coincide con `"resuelto"` (masculino) en el set.
   - Consecuencia: issues ya terminados se cuentan como "en progreso", inflando la carga de esa persona; `done_pts`/velocidad quedan en 0 aunque haya trabajo completado.
   - Jira expone la solución nativa: cada `status` incluye `statusCategory.key`, con valores estables e independientes del idioma (`"new"`, `"indeterminate"`, `"done"`). Confirmado en la respuesta real de la API.

2. **Velocidad y burndown a veces usan el tablero equivocado.** El código toma `client.get_boards(project_key)[0]`, el primer tablero devuelto por Jira. Verificado que proyectos distintos (AIC, THED, SATH, DEVOPSSP, y otros) comparten como primer resultado un tablero cruzado entre proyectos ("SW Ground MISC", id 9333), por lo que terminan mostrando el sprint de ese tablero compartido en vez del propio.

3. **Story Points casi no se usa en la organización.** De 12 proyectos con sprint activo revisados, solo 1 tenía Story Points cargados; los otros 11 estiman y registran el trabajo en horas (`timetracking`). Como `velocity.py` y `burndown.py` solo suman story points, el resultado es 0 para la gran mayoría de los equipos — no es un bug de campo mal mapeado, es que la métrica base no es la que usa la organización.

4. **Resumen: `epics_in_progress` usa un JQL con el nombre de estado fijo en inglés** (`status = "In Progress"`), que no existe como nombre literal en este Jira (los estados reales están en español, ej. `"En progreso"`). Confirmado que siempre devuelve 0. Existe una forma correcta verificada: `statusCategory = "In Progress"` funciona en JQL usando el nombre de categoría en inglés, independientemente del idioma del workflow.

## Decisiones de alcance

- **Carga de equipo:** se muestran **ambas vistas** por persona — carga del sprint activo y total de backlog sin resolver — no se reemplaza una por la otra.
- **Selección de tablero/sprint en Velocidad y Burndown:** selector explícito Proyecto → Tablero → Sprint, igual al patrón ya probado en Sprint Dashboard. No se intenta adivinar automáticamente como comportamiento principal.
- **Unidad de medida en Velocidad y Burndown:** horas (`timetracking`) como métrica principal, ya que es lo que usa casi toda la organización. Story points se muestran como dato secundario cuando existen, sin ser la base del cálculo.
- **Enfoque de implementación:** helpers compartidos + refactor dirigido (no se reescribe todo sobre el motor de Sprint Dashboard, ni se parchea cada archivo de forma aislada). Se corrige la causa raíz una sola vez y se reutiliza en los cinco routers afectados. Se mantienen los contratos JSON existentes donde es posible, para minimizar el impacto en el frontend.

## Diseño

### Componentes nuevos compartidos (`api/`)

- **`status_category.py`**
  - `categorize(status_field: dict) -> Literal["todo", "in_progress", "done"]`
  - Lee `status_field["statusCategory"]["key"]` y mapea `"new"→"todo"`, `"indeterminate"→"in_progress"`, `"done"→"done"`.
  - Si `statusCategory` falta o trae una clave desconocida, devuelve `"in_progress"` (nunca asume `"done"` por defecto, para no inflar el avance falsamente).

- **`effort.py`**
  - `extract_effort(fields: dict, sp_field: str) -> dict` con `committed_h`, `done_h`, `committed_sp`, `done_sp`.
  - Horas desde `timetracking.originalEstimateSeconds` / `timeoriginalestimate` (comprometido) y `timetracking.timeSpentSeconds` / `timespent` (hecho), convertidas a horas.
  - Story points desde `sp_field` (con fallback ya existente a `customfield_11934`).

- `constants.py` (los sets `DONE_STATUSES`/`TODO_STATUSES`/`IN_PROGRESS_STATUSES`) y `sprint_dashboard.py::_STATUS_MAP`/`_cat()` se eliminan, reemplazados por `status_category.categorize()` en los cinco routers (`overview`, `velocity`, `burndown`, `team`, `sprint_dashboard`).

### Cambios por router

**`overview.py`**
- `epics_in_progress`: JQL cambia de `status = "In Progress"` a `statusCategory = "In Progress"`.
- `sprint_done`: se calcula con `status_category.categorize(...) == "done"` en vez de comparar contra `DONE_STATUSES`.

**`velocity.py`**
- Acepta `board_id` opcional como query param en `/api/velocity/{project}` y `/dashboard/velocity`.
- Sin `board_id`: intenta un tablero cuya ubicación (`location.projectKey`) coincida exactamente con el proyecto antes de caer a `boards[0]` (red de seguridad, no la vía principal).
- `committed`/`completed` por sprint se calculan con `effort.extract_effort()`: `committed_h`/`done_h` son la métrica principal; `committed_sp`/`done_sp` se incluyen en la respuesta como datos secundarios cuando existan valores distintos de 0.
- "Completado" usa `status_category.categorize()`.

**`burndown.py`**
- Acepta `board_id` y `sprint_id` opcionales como query params en `/api/burndown/{project}` y `/dashboard/burndown`.
- Misma lógica de fallback de tablero que `velocity.py` cuando no se especifica.
- `total_pts`/`done_pts` pasan a basarse en horas (`total_h`/`done_h`) como serie principal del gráfico; se agregan `total_sp`/`done_sp` como datos secundarios opcionales.
- La curva "actual" sigue la misma lógica de interpolación ya existente, pero sobre horas en vez de story points.

**`team.py`**
- `get_team_data()` devuelve, por persona, dos bloques con la misma forma (`issues`, `story_points`/horas, `blocked`, `by_type`):
  - `sprint`: agregado de issues en los sprints activos de todos los tableros asociados al proyecto (sin selector de tablero — se combinan todos los sprints activos del proyecto).
  - `backlog`: comportamiento actual, todos los issues sin resolver del proyecto.
- Clasificación de bloqueados sigue igual (por nombre de status "blocked"/"bloqueado", no cambia).

**`sprint_dashboard.py`**
- `_cat()` y `_STATUS_MAP` se reemplazan por `status_category.categorize()`. Esto corrige el mismo bug de raíz (issues en `"Listo"` contados como en progreso) que hoy también afecta a este dashboard, aunque no fue mencionado explícitamente por el usuario.
- `_sp()` se reemplaza por `effort.extract_effort()` reutilizando la misma lógica que el resto de los routers.

### Frontend

- **`Velocity.jsx` / `Burndown.jsx`**: agregan selector Tablero → Sprint, reutilizando `getSprintBoards`/`getSprintSprints` de `jiraApi.js` (ya existen, usados hoy por `SprintDashboard.jsx`). Las llamadas a `getVelocity`/`getBurndown` incluyen `board_id`/`sprint_id` cuando el usuario los selecciona.
- Los gráficos relabelan el eje principal de "Story Points" a "Horas"; si hay story points disponibles, se muestran como anotación secundaria.
- **`TeamLoad.jsx`**: agrega un toggle "Sprint actual / Backlog total" que cambia qué bloque (`sprint` o `backlog`) se usa para las tarjetas de persona y el gráfico de barras. Por defecto se abre en "Sprint actual".

### Flujo de datos

```
Jira Server
  status.statusCategory.key ──→ status_category.categorize() ──→ overview, velocity, burndown, team, sprint_dashboard
  timetracking / customfield_10002|11934 ──→ effort.extract_effort() ──→ velocity, burndown, sprint_dashboard

Velocity/Burndown (frontend):
  selector Proyecto → Tablero → Sprint
    GET /api/velocity/{project}?board_id=X
    GET /api/burndown/{project}?board_id=X&sprint_id=Y

TeamLoad (frontend):
  toggle Sprint actual / Backlog total
    GET /api/team/{project}  →  { users: [[username, {sprint: {...}, backlog: {...}}], ...] }
```

## Manejo de errores y casos límite

- Proyecto sin tableros, o sin sprints activos/cerrados: estado vacío existente, sin cambios de comportamiento.
- Sprint sin ningún issue con horas ni story points cargados: 0 legítimo — se distingue de "0 por bug de mapeo", que es justamente lo que este diseño elimina.
- `statusCategory` ausente o con clave no reconocida: se clasifica como `"in_progress"`, nunca `"done"` por defecto, para no inflar falsamente el avance.
- `board_id`/`sprint_id` inválidos o que no pertenecen al proyecto: error 400 explícito, mismo patrón que ya usa `sprint_dashboard.py` ("Sprint not found").

## Testing

- `tests/conftest.py::make_issue` agrega un parámetro `category` (con default inferido del `status` recibido, para no romper tests existentes) que arma el bloque `statusCategory` realista.
- Tests nuevos para `status_category.categorize()` cubriendo los estados reales encontrados (`Listo`→done, `Resuelta`→done, `Cancelled`→done, `En progreso`→in_progress, `Por hacer`→todo, etc.) y el caso sin `statusCategory`.
- Tests nuevos para `effort.extract_effort()` cubriendo horas, story points, y ausencia de ambos.
- Tests actualizados de `test_velocity.py`/`test_burndown.py` para horas como base, story points como dato secundario, y los nuevos parámetros `board_id`/`sprint_id`.
- Tests nuevos de `test_team.py` para el doble scope (`sprint` vs `backlog`).
- Todo sigue mockeando `JiraClient` — no requiere credenciales reales para correr en CI.

## Fuera de alcance

- El dashboard de Backlog no se toca (no fue reportado como afectado).
- No se agregan nuevos KPIs ni gráficos; el trabajo es exclusivamente corrección de datos existentes.
- No se cambia el mecanismo de autenticación ni la configuración de conexión a Jira.
