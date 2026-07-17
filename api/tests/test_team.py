from unittest.mock import patch
from routers.team import get_team_data
from tests.conftest import make_issue


def _no_sprint_scope(mock_client):
    """Most tests don't care about the sprint-scoped block — no boards
    means _active_sprint_issues() returns an empty list cleanly."""
    mock_client.get_boards.return_value = []


@patch("routers.team.client")
def test_team_normal(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    _no_sprint_scope(mock_client)
    mock_client.search_issues.return_value = [
        make_issue("In Progress", assignee_name="alice", sp=5),
        make_issue("To Do", assignee_name="alice", sp=3),
        make_issue("To Do", assignee_name="bob", sp=8),
    ]

    result = get_team_data("PROJ")

    assert result["total_issues"] == 3
    users = dict(result["users"])
    assert users["alice"]["backlog"]["issues"] == 2
    assert users["alice"]["backlog"]["story_points"] == 8
    assert users["bob"]["backlog"]["issues"] == 1
    assert users["bob"]["backlog"]["story_points"] == 8


@patch("routers.team.client")
def test_team_no_assignee(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    _no_sprint_scope(mock_client)
    mock_client.search_issues.return_value = [
        make_issue("To Do", assignee_name=None, sp=5),
    ]

    result = get_team_data("PROJ")

    users = dict(result["users"])
    assert "_unassigned" in users
    assert users["_unassigned"]["display"] == "Sin asignar"
    assert users["_unassigned"]["backlog"]["issues"] == 1


@patch("routers.team.client")
def test_team_no_story_points(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    _no_sprint_scope(mock_client)
    mock_client.search_issues.return_value = [
        make_issue("To Do", assignee_name="alice", sp=None),
    ]

    result = get_team_data("PROJ")

    users = dict(result["users"])
    assert users["alice"]["backlog"]["story_points"] == 0


@patch("routers.team.client")
def test_team_hours_summed(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    _no_sprint_scope(mock_client)
    mock_client.search_issues.return_value = [
        make_issue("In Progress", assignee_name="alice", orig_s=4 * 3600),
    ]

    result = get_team_data("PROJ")

    users = dict(result["users"])
    assert users["alice"]["backlog"]["hours"] == 4.0


@patch("routers.team.client")
def test_team_empty_project(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    _no_sprint_scope(mock_client)
    mock_client.search_issues.return_value = []

    result = get_team_data("PROJ")

    assert result["total_issues"] == 0
    assert result["users"] == []


@patch("routers.team.client")
def test_team_blocked_counted(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    _no_sprint_scope(mock_client)
    mock_client.search_issues.return_value = [
        make_issue("Blocked", assignee_name="alice", sp=2),
        make_issue("In Progress", assignee_name="alice", sp=3),
    ]

    result = get_team_data("PROJ")

    users = dict(result["users"])
    assert users["alice"]["backlog"]["blocked"] == 1


@patch("routers.team.client")
def test_team_api_error(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.search_issues.side_effect = Exception("timeout")

    result = get_team_data("PROJ")

    assert result["total_issues"] == 0
    assert result["users"] == []


@patch("routers.team.client")
def test_team_sprint_scope_separate_from_backlog(mock_client):
    """Someone who owns a lot of historical backlog issues but has little
    work in the active sprint should not look 'abnormal' in the sprint view."""
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [{"id": 1, "name": "Board 1", "type": "scrum"}]
    mock_client.get_sprints.return_value = [{"id": 100, "state": "active", "name": "Sprint 1"}]

    backlog_issues = [make_issue(f"To Do-{n}", key=f"PROJ-{n}", assignee_name="alice") for n in range(20)]
    sprint_issue = make_issue("In Progress", key="PROJ-1", assignee_name="alice", project_key="PROJ")

    def search_issues(jql, fields=None, max_results=100):
        return backlog_issues

    mock_client.search_issues.side_effect = search_issues
    mock_client.get_sprint_issues.return_value = [sprint_issue]

    result = get_team_data("PROJ")

    users = dict(result["users"])
    assert users["alice"]["backlog"]["issues"] == 20
    assert users["alice"]["sprint"]["issues"] == 1


@patch("routers.team.client")
def test_team_sprint_scope_filters_out_other_projects(mock_client):
    """Boards can be shared across many projects — issues from other
    projects in the same active sprint must not leak into this project's
    sprint-scoped workload."""
    mock_client.get_story_points_field.return_value = "customfield_10002"
    _no_sprint_scope_boards = [{"id": 1, "name": "Shared board", "type": "scrum"}]
    mock_client.get_boards.return_value = _no_sprint_scope_boards
    mock_client.get_sprints.return_value = [{"id": 100, "state": "active", "name": "Sprint 1"}]
    mock_client.search_issues.return_value = []
    mock_client.get_sprint_issues.return_value = [
        make_issue("In Progress", key="PROJ-1", assignee_name="alice", project_key="PROJ"),
        make_issue("In Progress", key="OTHER-1", assignee_name="alice", project_key="OTHER"),
    ]

    result = get_team_data("PROJ")

    users = dict(result["users"])
    assert users["alice"]["sprint"]["issues"] == 1
