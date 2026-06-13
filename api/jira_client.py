import urllib3
import requests
from config import settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class JiraClient:
    def __init__(self):
        self.base_url = settings.jira_base_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (settings.jira_user, settings.jira_password)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        self.session.verify = False

    # ── HTTP primitives ───────────────────────────────────────────────────────

    def _get(self, path: str, params: dict = None) -> dict:
        r = self.session.get(f"{self.base_url}{path}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, payload: dict) -> dict:
        r = self.session.post(f"{self.base_url}{path}", json=payload, timeout=30)
        if not r.ok:
            raise requests.HTTPError(
                f"HTTP {r.status_code} — {r.text[:400]}", response=r
            )
        return r.json() if r.content else {}

    def _put(self, path: str, payload: dict) -> dict:
        r = self.session.put(f"{self.base_url}{path}", json=payload, timeout=30)
        r.raise_for_status()
        return r.json() if r.content else {}

    def _delete(self, path: str) -> None:
        r = self.session.delete(f"{self.base_url}{path}", timeout=30)
        r.raise_for_status()

    # ── Identity ──────────────────────────────────────────────────────────────

    def get_myself(self) -> dict:
        return self._get("/rest/api/2/myself")

    # ── Projects ──────────────────────────────────────────────────────────────

    def get_all_projects(self) -> list:
        return self._get("/rest/api/2/project") or []

    def get_project(self, project_key: str) -> dict:
        return self._get(f"/rest/api/2/project/{project_key}")

    # ── Issues ────────────────────────────────────────────────────────────────

    def search_issues(
        self,
        jql: str,
        fields: list = None,
        max_results: int = 100,
    ) -> list:
        """Paginated JQL search — fetches all pages automatically."""
        default_fields = [
            "summary", "status", "assignee", "priority", "issuetype", "project",
            "customfield_10002",   # Story Points (Alcatel)
            "customfield_11934",   # Original Story Points (historical)
            "timetracking", "timespent", "timeoriginalestimate",
        ]
        all_issues: list = []
        start_at = 0
        while True:
            payload = {
                "jql": jql,
                "maxResults": max_results,
                "startAt": start_at,
                "fields": fields or default_fields,
            }
            result = self._post("/rest/api/2/search", payload)
            batch = result.get("issues", [])
            all_issues.extend(batch)
            total = result.get("total", 0)
            start_at += len(batch)
            if not batch or start_at >= total:
                break
        return all_issues

    def get_issue(self, issue_key: str) -> dict:
        return self._get(f"/rest/api/2/issue/{issue_key}")

    def create_issue(
        self,
        project_key: str,
        summary: str,
        issue_type: str,
        description: str = "",
        priority: str = "Medium",
        story_points: int = None,
        assignee_name: str = None,
        parent_key: str = None,
    ) -> dict:
        fields: dict = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
            "description": description or summary,
        }
        if story_points is not None:
            fields["customfield_10002"] = story_points
        if assignee_name:
            fields["assignee"] = {"name": assignee_name}
        if parent_key:
            fields["parent"] = {"key": parent_key}
        return self._post("/rest/api/2/issue", {"fields": fields})

    def update_issue(self, issue_key: str, fields: dict) -> dict:
        return self._put(f"/rest/api/2/issue/{issue_key}", {"fields": fields})

    def get_transitions(self, issue_key: str) -> list:
        return self._get(f"/rest/api/2/issue/{issue_key}/transitions").get("transitions", [])

    def transition_issue(self, issue_key: str, transition_id: str) -> None:
        self._post(
            f"/rest/api/2/issue/{issue_key}/transitions",
            {"transition": {"id": transition_id}},
        )

    # ── Users ─────────────────────────────────────────────────────────────────

    def get_users(self, project_key: str) -> list:
        result = self._get(
            "/rest/api/2/user/assignable/search",
            {"project": project_key, "maxResults": 50},
        )
        return result if isinstance(result, list) else []

    # ── Boards & Sprints (Agile API) ──────────────────────────────────────────

    def get_all_boards(self, board_type: str = "scrum") -> list:
        """Paginated fetch of all boards of a given type."""
        all_boards: list = []
        start = 0
        while True:
            result = self._get("/rest/agile/1.0/board", {
                "type": board_type,
                "maxResults": 50,
                "startAt": start,
            })
            values = result.get("values", [])
            all_boards.extend(values)
            if result.get("isLast", True) or not values:
                break
            start += len(values)
        return all_boards

    def get_board_configuration(self, board_id: int) -> dict:
        return self._get(f"/rest/agile/1.0/board/{board_id}/configuration")

    def get_boards(self, project_key: str) -> list:
        """Paginated fetch of boards for a specific project."""
        all_boards: list = []
        start = 0
        while True:
            result = self._get("/rest/agile/1.0/board", {
                "projectKeyOrId": project_key,
                "maxResults": 50,
                "startAt": start,
            })
            values = result.get("values", [])
            all_boards.extend(values)
            if result.get("isLast", True) or not values:
                break
            start += len(values)
        return all_boards

    def get_sprints(self, board_id: int, state: str = None) -> list:
        """Paginated sprint fetch for a board."""
        params: dict = {"maxResults": 50}
        if state:
            params["state"] = state
        all_sprints: list = []
        start = 0
        while True:
            params["startAt"] = start
            try:
                result = self._get(f"/rest/agile/1.0/board/{board_id}/sprint", params)
            except Exception:
                break
            values = result.get("values", [])
            all_sprints.extend(values)
            if result.get("isLast", True) or not values:
                break
            start += len(values)
        return all_sprints

    def get_sprint_issues(self, sprint_id: int) -> list:
        return self.get_sprint_issues_by_jql(sprint_id)

    def get_sprint_issues_by_jql(self, sprint_id: int) -> list:
        return self.search_issues(
            jql=f"sprint = {sprint_id}",
            fields=[
                "summary", "status", "assignee", "priority", "issuetype", "project",
                "customfield_10002", "customfield_11934",
                "timetracking", "timespent", "timeoriginalestimate",
            ],
        )

    def create_sprint(
        self,
        board_id: int,
        name: str,
        start_date: str = None,
        end_date: str = None,
    ) -> dict:
        payload: dict = {"name": name, "originBoardId": board_id}
        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date
        return self._post("/rest/agile/1.0/sprint", payload)

    def update_sprint(self, sprint_id: int, payload: dict) -> dict:
        return self._put(f"/rest/agile/1.0/sprint/{sprint_id}", payload)

    def move_issues_to_sprint(self, sprint_id: int, issue_keys: list) -> None:
        self._post(
            f"/rest/agile/1.0/sprint/{sprint_id}/issue",
            {"issues": issue_keys},
        )

    # ── Versions ──────────────────────────────────────────────────────────────

    def get_versions(self, project_key: str) -> list:
        return self._get(f"/rest/api/2/project/{project_key}/versions")

    # ── Field helpers ─────────────────────────────────────────────────────────

    def get_story_points_field(self) -> str:
        try:
            fields = self._get("/rest/api/2/field")
            for f in fields:
                if f.get("name", "").lower() == "story points":
                    return f["id"]
        except Exception:
            pass
        return "customfield_10002"

    def is_healthy(self) -> bool:
        try:
            self.get_myself()
            return True
        except Exception:
            return False
