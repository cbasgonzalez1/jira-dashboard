from unittest.mock import patch
from routers.overview import get_overview_data
from tests.conftest import make_issue


def _search_side_effect(open_issues, sprint_issues, bugs, unassigned, epics):
    """Return the right dataset based on JQL content."""
    def side_effect(jql, fields=None, max_results=100):
        if "sprint in openSprints()" in jql:
            return sprint_issues
        if "issuetype = Bug" in jql:
            return bugs
        if "assignee is EMPTY" in jql:
            return unassigned
        if "issuetype = Epic" in jql:
            return epics
        return open_issues
    return side_effect


@patch("routers.overview.client")
def test_overview_normal(mock_client):
    mock_client.get_all_projects.return_value = [{"key": "PROJ", "name": "Project"}]
    mock_client.search_issues.side_effect = _search_side_effect(
        open_issues=[make_issue("Open"), make_issue("Open")],
        sprint_issues=[make_issue("Done"), make_issue("In Progress")],
        bugs=[make_issue("Open", itype="Bug")],
        unassigned=[make_issue("Open")],
        epics=[make_issue("In Progress", itype="Epic")],
    )

    result = get_overview_data()

    assert result["active_projects"] == 1
    assert result["total_open"] == 2
    assert result["total_critical_bugs"] == 1
    assert result["total_unassigned"] == 1
    assert result["total_epics_in_progress"] == 1
    assert result["projects"][0]["sprint_done"] == 1
    assert result["projects"][0]["sprint_total"] == 2
    assert result["projects"][0]["sprint_pct"] == 50


@patch("routers.overview.client")
def test_overview_empty_projects(mock_client):
    mock_client.get_all_projects.return_value = []

    result = get_overview_data()

    assert result["active_projects"] == 0
    assert result["projects"] == []
    assert result["total_open"] == 0


@patch("routers.overview.client")
def test_overview_get_projects_fails(mock_client):
    mock_client.get_all_projects.side_effect = Exception("connection refused")

    result = get_overview_data()

    assert result["active_projects"] == 0
    assert result["projects"] == []


@patch("routers.overview.client")
def test_overview_one_project_fails(mock_client):
    mock_client.get_all_projects.return_value = [
        {"key": "OK", "name": "Good Project"},
        {"key": "FAIL", "name": "Bad Project"},
    ]

    def selective_fail(jql, fields=None, max_results=100):
        if "FAIL" in jql:
            raise Exception("timeout")
        return []

    mock_client.search_issues.side_effect = selective_fail

    result = get_overview_data()

    assert result["active_projects"] == 1
    assert result["projects"][0]["key"] == "OK"


@patch("routers.overview.client")
def test_overview_no_sprint_issues(mock_client):
    mock_client.get_all_projects.return_value = [{"key": "PROJ", "name": "Project"}]
    mock_client.search_issues.side_effect = _search_side_effect(
        open_issues=[make_issue("Open")],
        sprint_issues=[],
        bugs=[],
        unassigned=[],
        epics=[],
    )

    result = get_overview_data()

    assert result["projects"][0]["sprint_total"] == 0
    assert result["projects"][0]["sprint_done"] == 0
    assert result["projects"][0]["sprint_pct"] == 0


@patch("routers.overview.client")
def test_overview_multiple_projects_totals(mock_client):
    mock_client.get_all_projects.return_value = [
        {"key": "A", "name": "Alpha"},
        {"key": "B", "name": "Beta"},
    ]

    def by_project(jql, fields=None, max_results=100):
        if "sprint in openSprints()" in jql:
            return []
        if "issuetype = Bug" in jql:
            return []
        if "assignee is EMPTY" in jql:
            return []
        if "issuetype = Epic" in jql:
            return []
        # open_issues: both projects return 3
        return [make_issue("Open")] * 3

    mock_client.search_issues.side_effect = by_project

    result = get_overview_data()

    assert result["active_projects"] == 2
    assert result["total_open"] == 6
