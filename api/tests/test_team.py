from unittest.mock import patch
from routers.team import get_team_data
from tests.conftest import make_issue


@patch("routers.team.client")
def test_team_normal(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.search_issues.return_value = [
        make_issue("In Progress", assignee_name="alice", sp=5),
        make_issue("To Do", assignee_name="alice", sp=3),
        make_issue("To Do", assignee_name="bob", sp=8),
    ]

    result = get_team_data("PROJ")

    assert result["total_issues"] == 3
    users = dict(result["users"])
    assert users["alice"]["issues"] == 2
    assert users["alice"]["story_points"] == 8
    assert users["bob"]["issues"] == 1
    assert users["bob"]["story_points"] == 8


@patch("routers.team.client")
def test_team_no_assignee(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.search_issues.return_value = [
        make_issue("To Do", assignee_name=None, sp=5),
    ]

    result = get_team_data("PROJ")

    users = dict(result["users"])
    assert "_unassigned" in users
    assert users["_unassigned"]["display"] == "Sin asignar"
    assert users["_unassigned"]["issues"] == 1


@patch("routers.team.client")
def test_team_no_story_points(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.search_issues.return_value = [
        make_issue("To Do", assignee_name="alice", sp=None),
    ]

    result = get_team_data("PROJ")

    users = dict(result["users"])
    assert users["alice"]["story_points"] == 0


@patch("routers.team.client")
def test_team_no_time_tracking_ignored(mock_client):
    """team router does not use timetracking — test that it handles absent fields."""
    mock_client.get_story_points_field.return_value = "customfield_10002"
    issue = make_issue("In Progress", assignee_name="alice", sp=3, orig_s=0, rem_s=0, spent_s=0)
    issue["fields"]["timetracking"] = {}
    mock_client.search_issues.return_value = [issue]

    result = get_team_data("PROJ")

    assert result["total_issues"] == 1


@patch("routers.team.client")
def test_team_empty_project(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.search_issues.return_value = []

    result = get_team_data("PROJ")

    assert result["total_issues"] == 0
    assert result["users"] == []


@patch("routers.team.client")
def test_team_blocked_counted(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.search_issues.return_value = [
        make_issue("Blocked", assignee_name="alice", sp=2),
        make_issue("In Progress", assignee_name="alice", sp=3),
    ]

    result = get_team_data("PROJ")

    users = dict(result["users"])
    assert users["alice"]["blocked"] == 1


@patch("routers.team.client")
def test_team_api_error(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.search_issues.side_effect = Exception("timeout")

    result = get_team_data("PROJ")

    assert result["total_issues"] == 0
    assert result["users"] == []
