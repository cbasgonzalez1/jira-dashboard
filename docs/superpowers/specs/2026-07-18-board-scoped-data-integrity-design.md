# Integridad de datos: alcance real por tablero y eliminación de datos de demo

**Fecha:** 2026-07-18
**Estado:** Aprobado para planificación

## Contexto

Tras el fix de la sesión anterior (filtrar por proyecto en Velocity/Burndown/Team), el usuario reportó dos problemas nuevos al revisar los dashboards contra Jira real:

1. Al abrir Sprint Dashboard antes de elegir board/sprint, la pantalla mostraba proyectos "CRM", "SCRUM", "INF", "SEC" — nombres que no existen en el Jira real.
2. En Velocity/Burndown, cambiar el selector de Tablero (para el mismo proyecto) no cambia los números mostrados — siempre las mismas horas sin importar qué tablero se elija.

Se investigó ambos contra la instancia real antes de proponer una solución.

## Causas raíz confirmadas

1. **`SprintDashboard.jsx` tiene un objeto `DEMO_DATA` hardcodeado** (KPIs, personas y proyectos ficticios — `SCRUM`/`CRM`/`INF`/`SEC`, sobrantes de un dataset de demo de antes de conectar la app al Jira real) que se muestra automáticamente mientras no hay board+sprint seleccionados. `api/seed/` contiene ese mismo dataset ficticio pero no está importado por ningún router — solo el frontend lo reproduce.

2. **El tablero seleccionado no acota qué issues se cuentan.** `jira_client.get_sprint_issues()` usa la búsqueda JQL global `sprint = {id}`, que ignora completamente desde qué tablero se está mirando. El fix de la sesión anterior agregó un filtro por `project.key` encima de eso, pero como muchos tableros de esta organización comparten el mismo calendario de sprints (mismo `sprint_id` en decenas de tableros — confirmado), el resultado para un proyecto dado termina siendo idéntico sin importar el tablero elegido.

   Verificado contra Jira real que esto **no debería ser así**: el endpoint nativo de Jira que sí respeta el filtro propio de cada tablero (`GET /rest/agile/1.0/board/{board_id}/sprint/{sprint_id}/issue`) devuelve, para el mismo sprint 12984 en el proyecto DEVOPSSP:
   - Tablero "DevOps Spain" (5505, propio del proyecto): 13 issues, las 13 de DEVOPSSP.
   - Tablero compartido "SW Ground MISC" (9333): 65 issues de 7 proyectos, 10 de DEVOPSSP.
   - Tablero compartido "SW Ground Segment" (5493): 95 issues de 9 proyectos, 12 de DEVOPSSP.

   El filtro propio de cada tablero (por proyecto, componente o asignado — confirmado leyendo el JQL real de sus filtros) es la categorización por "equipo/tablero" que el usuario espera ver. `sprint_dashboard.py` tiene el mismo problema: recibe `board_id` pero no lo usa para acotar los issues, solo para leer metadata del sprint.

3. **Backlog cuenta "sin estimar" mirando solo story points**, el mismo patrón horas-vs-puntos ya corregido en Velocity/Burndown/Team pero que quedó afuera en este router.

## Decisiones de alcance

- **Fuente de issues por sprint pasa a ser el endpoint de tablero de Jira**, no la búsqueda JQL global. Esto aplica a los cuatro routers que iteran issues de un sprint: `velocity.py`, `burndown.py`, `team.py`, `sprint_dashboard.py`.
- El filtro por `project.key` (agregado la sesión anterior en `velocity.py`/`burndown.py`) **se mantiene** como red de seguridad — un tablero puede seguir abarcando varios proyectos, y Velocity/Burndown siguen siendo por-proyecto. `sprint_dashboard.py` y `team.py` no filtran por proyecto porque su propósito es mostrar todo lo que el tablero/proyecto trae consigo (`by_project` desglosado, o el conjunto de tableros propios del proyecto).
- **`DEMO_DATA` se elimina por completo.** Sin board+sprint seleccionados, se muestra un estado vacío explícito ("Seleccioná un board y un sprint"), igual al patrón ya usado en Burndown para "sin sprint activo".
- El regex `/^(SCRUM|CRM|INF)\s/` en `Velocity.jsx` y `VelocityChart.jsx` se elimina — no corresponde a ningún dato real de este Jira, los nombres de sprint se muestran tal cual vienen de la API.
- **Backlog**: "sin estimar" pasa a ser "sin story points **y** sin horas comprometidas", usando `effort.extract_effort()` (ya existente, reutilizado en todos los demás routers).

## Diseño

### `jira_client.py`

Nuevo método:

```python
def get_board_sprint_issues(self, board_id: int, sprint_id: int) -> list:
    """Issues de un sprint tal como los ve un tablero específico — respeta
    el filtro propio del tablero (proyecto/asignado/componente), a
    diferencia de la búsqueda JQL global `sprint = X` que no sabe desde
    qué tablero se está mirando."""
```

Pagina con `startAt`/`total` sobre `GET /rest/agile/1.0/board/{board_id}/sprint/{sprint_id}/issue`, mismo `fields` por default que `get_sprint_issues_by_jql`. `get_sprint_issues()`/`get_sprint_issues_by_jql()` no se tocan (se mantienen para los tests existentes y cualquier otro caller que sí quiera la vista global).

### Routers

- **`velocity.py`** (`get_velocity_data`): dentro del loop de sprints, `client.get_sprint_issues(sprint["id"])` → `client.get_board_sprint_issues(selected_board_id, sprint["id"])`. `_sprint_effort(issues, sp_field, project_key)` no cambia de firma.
- **`burndown.py`** (`get_burndown_data`): mismo cambio, `client.get_sprint_issues(selected_sprint_id)` → `client.get_board_sprint_issues(selected_board_id, selected_sprint_id)`.
- **`team.py`** (`_active_sprint_issues`): dentro del loop `for board in boards: for sprint in active_sprints:`, `client.get_sprint_issues(sprint["id"])` → `client.get_board_sprint_issues(board["id"], sprint["id"])`. El filtro por `project.key` que ya tiene esta función se mantiene sin cambios.
- **`sprint_dashboard.py`** (`dashboard_data`): `client.get_sprint_issues_by_jql(sprint_id)` → `client.get_board_sprint_issues(board_id, sprint_id)` (usa el `board_id` que el endpoint ya recibe como parámetro obligatorio y hasta ahora no usaba para esto).
- **`backlog.py`** (`get_backlog_data`): agrega `timetracking`/`timespent`/`timeoriginalestimate` a los `fields` pedidos; `unestimated` pasa de `not f.get(sp_field)` a `not f.get(sp_field) and extract_effort(f, sp_field)["committed_h"] == 0`.

### Frontend

- **`SprintDashboard.jsx`**: se elimina `DEMO_DATA` (líneas 39-69) y la variable `isDemo`. `displayData` pasa a ser simplemente `data ?? null`. Nuevo bloque de estado vacío (mismo estilo que `boardHasNoSprints`) para cuando `!boardId || !sprintId`, con texto "Seleccioná un board y un sprint para ver datos reales de Jira".
- **`Velocity.jsx`** (líneas 85 y 133) y **`VelocityChart.jsx`** (línea 33): se elimina `.replace(/^(SCRUM|CRM|INF)\s/, '')`, se usa `s.name`/`bestSprint.name` tal cual.

### Flujo de datos

```
Jira Server
  GET /board/{board_id}/sprint/{sprint_id}/issue   (respeta filtro propio del tablero)
    → velocity.py, burndown.py, team.py, sprint_dashboard.py

Selector Tablero (Velocity/Burndown) o Board (Sprint Dashboard):
  cambiar de tablero para el mismo proyecto ahora sí cambia los números,
  porque Jira devuelve un conjunto de issues distinto por tablero.
```

## Manejo de errores y casos límite

- Un tablero sin issues en ese sprint (filtro propio no matchea nada del proyecto): 0 legítimo, mismo tratamiento que hoy.
- `get_board_sprint_issues` con `board_id`/`sprint_id` que no coinciden (sprint no pertenece a ese tablero): Jira devuelve error HTTP — se deja propagar igual que otras llamadas del cliente (los routers ya capturan excepciones a nivel función y devuelven el estado vacío).
- Sprint Dashboard sin board+sprint seleccionados: estado vacío explícito, no fetch a `/api/sprint-dashboard/data` (ya es así vía `enabled: !!(boardId && sprintId)`; solo cambia qué se renderiza mientras tanto).

## Testing

- Tests de `test_velocity.py`, `test_burndown.py`, `test_team.py`, `test_sprint_dashboard.py`: reemplazar los mocks de `mock_client.get_sprint_issues`/`get_sprint_issues_by_jql` por `mock_client.get_board_sprint_issues`, verificando que se llama con `(board_id, sprint_id)` correctos.
- Test nuevo en `test_backlog.py`: issue con horas cargadas pero sin story points no debe contar como "sin estimar".
- No se agrega test unitario para `get_board_sprint_issues` en sí (paginación HTTP) — mismo criterio que el resto de `jira_client.py`, que no tiene tests directos; se prueba a través de los routers que lo consumen (mockeados) y contra Jira real como smoke test manual.
- Sin test suite de frontend en este proyecto — la eliminación de `DEMO_DATA` se verifica manualmente (captura de pantalla) igual que la sesión anterior.

## Fuera de alcance

- No se toca `get_sprint_issues`/`get_sprint_issues_by_jql` — se mantienen para no romper ningún caller o test que dependa de la vista global.
- No se agrega selector de tablero a Backlog (no fue reportado como afectado, y Backlog no usa boards/sprints).
- No se cambia el mecanismo de autenticación ni la configuración de conexión a Jira.
