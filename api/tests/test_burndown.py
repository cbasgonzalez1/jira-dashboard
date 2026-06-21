from unittest.mock import patch
from routers.burndown import get_burndown_data
from tests.conftest import make_issue, make_board, make_sprint


@patch("routers.burndown.client")
def test_burndown_normal(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board()]
    sprint = make_sprint(
        sid=10, name="Sprint 1", state="active",
        start="2026-06-01T00:00:00+00:00",
        end="2026-06-14T00:00:00+00:00",
    )
    mock_client.get_sprints.return_value = [sprint]
    mock_client.get_sprint_issues.return_value = [
        make_issue("Done", sp=5),
        make_issue("In Progress", sp=3),
    ]

    result = get_burndown_data("PROJ")

    assert result["sprint"] == "Sprint 1"
    assert result["total_pts"] == 8
    assert result["done_pts"] == 5
    assert result["remaining_pts"] == 3
    assert len(result["days"]) == 14  # 13 days + 1 = 14 entries
    assert len(result["ideal"]) == 14
    assert len(result["actual"]) == 14
    assert result["ideal"][0] == 8.0
    assert result["ideal"][-1] == 0.0


@patch("routers.burndown.client")
def test_burndown_no_boards(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = []

    result = get_burndown_data("PROJ")

    assert result["sprint"] is None
    assert result["days"] == []


@patch("routers.burndown.client")
def test_burndown_no_active_sprint(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board()]
    mock_client.get_sprints.return_value = []

    result = get_burndown_data("PROJ")

    assert result["sprint"] is None


@patch("routers.burndown.client")
def test_burndown_no_story_points(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board()]
    mock_client.get_sprints.return_value = [make_sprint()]
    mock_client.get_sprint_issues.return_value = [
        make_issue("Done", sp=None),
        make_issue("In Progress", sp=None),
    ]

    result = get_burndown_data("PROJ")

    assert result["total_pts"] == 0
    assert result["done_pts"] == 0
    assert result["ideal"][0] == 0.0


@patch("routers.burndown.client")
def test_burndown_sprint_without_issues(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board()]
    mock_client.get_sprints.return_value = [make_sprint()]
    mock_client.get_sprint_issues.return_value = []

    result = get_burndown_data("PROJ")

    assert result["total_pts"] == 0
    assert result["done_pts"] == 0


@patch("routers.burndown.client")
def test_burndown_api_error(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.side_effect = Exception("timeout")

    result = get_burndown_data("PROJ")

    assert result["sprint"] is None
    assert result["days"] == []


@patch("routers.burndown.client")
def test_burndown_total_days_range_consistency(mock_client):
    """days, ideal, and actual must all have the same length (total_days_range)."""
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board()]
    mock_client.get_sprints.return_value = [make_sprint(
        start="2026-06-01T00:00:00+00:00",
        end="2026-06-11T00:00:00+00:00",
    )]
    mock_client.get_sprint_issues.return_value = [make_issue("Done", sp=10)]

    result = get_burndown_data("PROJ")

    assert len(result["days"]) == len(result["ideal"]) == len(result["actual"])
    assert len(result["days"]) == 11  # 10 days + 1
