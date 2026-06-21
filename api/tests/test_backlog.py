from unittest.mock import patch
from routers.backlog import get_backlog_data
from tests.conftest import make_issue


@patch("routers.backlog.client")
def test_backlog_normal(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.search_issues.return_value = [
        make_issue("To Do", "Story", sp=3),
        make_issue("To Do", "Bug", sp=None),
        make_issue("In Progress", "Task", sp=5),
    ]

    result = get_backlog_data("PROJ")

    assert result["total"] == 3
    assert result["unestimated"] == 1
    assert result["by_type"]["Story"] == 1
    assert result["by_type"]["Bug"] == 1
    assert result["by_type"]["Task"] == 1
    assert result["project"] == "PROJ"


@patch("routers.backlog.client")
def test_backlog_no_issues(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.search_issues.return_value = []

    result = get_backlog_data("EMPTY")

    assert result["total"] == 0
    assert result["unestimated"] == 0
    assert result["by_type"] == {}


@patch("routers.backlog.client")
def test_backlog_no_story_points(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.search_issues.return_value = [
        make_issue("To Do", sp=None),
        make_issue("To Do", sp=None),
    ]

    result = get_backlog_data("PROJ")

    assert result["unestimated"] == 2


@patch("routers.backlog.client")
def test_backlog_api_error(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.search_issues.side_effect = Exception("Jira unavailable")

    result = get_backlog_data("PROJ")

    assert result["total"] == 0
    assert result["project"] == "PROJ"


@patch("routers.backlog.client")
def test_backlog_no_assignee_field_ignored(mock_client):
    """Backlog groups by type/priority/status, not assignee — None assignee is fine."""
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.search_issues.return_value = [
        make_issue("To Do", assignee_name=None, sp=2),
    ]

    result = get_backlog_data("PROJ")

    assert result["total"] == 1
    assert result["unestimated"] == 0
