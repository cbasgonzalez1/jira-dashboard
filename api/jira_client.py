import httpx
from config import settings


class JiraClient:
    def __init__(self):
        self.base_url = settings.jira_base_url
        self.auth = httpx.BasicAuth(settings.jira_user, settings.jira_api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{self.base_url}{path}"
        r = httpx.get(url, auth=self.auth, headers=self.headers, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        r = httpx.post(url, auth=self.auth, headers=self.headers, json=payload, timeout=30)
        if not r.is_success:
            raise httpx.HTTPStatusError(
                f"HTTP {r.status_code} — {r.text[:400]}",
                request=r.request,
                response=r,
            )
        return r.json() if r.content else {}

    def _put(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        r = httpx.put(url, auth=self.auth, headers=self.headers, json=payload, timeout=30)
        r.raise_for_status()
        return r.json() if r.content else {}

    # ── Identity ──────────────────────────────────────────────────────────────

    def get_myself(self) -> dict:
        return self._get("/rest/api/3/myself")

    # ── Projects ──────────────────────────────────────────────────────────────

    def get_all_projects(self) -> list:
        result = self._get("/rest/api/3/project/search")
        return result.get("values", [])

    def get_project(self, project_key: str) -> dict:
        return self._get(f"/rest/api/3/project/{project_key}")

    # ── Issues ────────────────────────────────────────────────────────────────

    def search_issues(self, jql: str, fields: list = None, max_results: int = 100) -> list:
        payload = {
            "jql": jql,
            "maxResults": max_results,
            "fields": fields or [
                "summary", "status", "assignee", "priority",
                "issuetype", "story_points", "created", "updated", "parent",
                "customfield_10016",  # story points (next-gen)
                "customfield_10028",  # story points (classic)
            ],
        }
        result = self._post("/rest/api/3/search/jql", payload)
        return result.get("issues", [])

    def get_issue(self, issue_key: str) -> dict:
        return self._get(f"/rest/api/3/issue/{issue_key}")

    def create_issue(
        self,
        project_key: str,
        summary: str,
        issue_type: str,
        description: str = "",
        priority: str = "Medium",
        story_points: int = None,
        assignee_id: str = None,
        parent_key: str = None,
    ) -> dict:
        fields: dict = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description or summary}],
                    }
                ],
            },
        }
        if story_points is not None:
            fields["story_points"] = story_points
        if assignee_id:
            fields["assignee"] = {"accountId": assignee_id}
        if parent_key:
            fields["parent"] = {"key": parent_key}

        return self._post("/rest/api/3/issue", {"fields": fields})

    def update_issue(self, issue_key: str, fields: dict) -> dict:
        return self._put(f"/rest/api/3/issue/{issue_key}", {"fields": fields})

    def get_transitions(self, issue_key: str) -> list:
        result = self._get(f"/rest/api/3/issue/{issue_key}/transitions")
        return result.get("transitions", [])

    def transition_issue(self, issue_key: str, transition_id: str) -> None:
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
        r = httpx.post(
            url,
            auth=self.auth,
            headers=self.headers,
            json={"transition": {"id": transition_id}},
            timeout=30,
        )
        r.raise_for_status()

    # ── Users ─────────────────────────────────────────────────────────────────

    def get_users(self, project_key: str) -> list:
        result = self._get(
            "/rest/api/3/user/assignable/search",
            {"project": project_key, "maxResults": 50},
        )
        return result if isinstance(result, list) else []

    # ── Boards & Sprints (Agile API) ──────────────────────────────────────────

    def get_all_boards(self) -> list:
        result = self._get("/rest/agile/1.0/board", {"maxResults": 50})
        return result.get("values", [])

    def get_boards(self, project_key: str) -> list:
        result = self._get("/rest/agile/1.0/board", {"projectKeyOrId": project_key})
        return result.get("values", [])

    def get_sprints(self, board_id: int, state: str = None) -> list:
        params = {}
        if state:
            params["state"] = state
        result = self._get(f"/rest/agile/1.0/board/{board_id}/sprint", params)
        return result.get("values", [])

    def get_sprint_issues(self, sprint_id: int) -> list:
        result = self._get(f"/rest/agile/1.0/sprint/{sprint_id}/issue")
        return result.get("issues", [])

    def get_sprint_issues_by_jql(self, sprint_id: int) -> list:
        return self.search_issues(
            jql=f"sprint = {sprint_id}",
            fields=[
                "summary", "status", "assignee", "priority", "issuetype", "project",
                "customfield_10016", "customfield_10028",
                "timetracking", "timespent", "timeoriginalestimate", "aggregatetimeremaining",
            ],
            max_results=500,
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
        return self._get(f"/rest/api/3/project/{project_key}/versions")

    # ── Field helpers ─────────────────────────────────────────────────────────

    def get_story_points_field(self) -> str:
        """Return the custom field ID for Story Points (varies by instance)."""
        try:
            fields = self._get("/rest/api/3/field")
            for f in fields:
                if f.get("name", "").lower() == "story points":
                    return f["id"]
        except Exception:
            pass
        return "customfield_10016"

    def is_healthy(self) -> bool:
        try:
            self.get_myself()
            return True
        except Exception:
            return False
