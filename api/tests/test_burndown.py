from unittest.mock import patch
from routers.burndown import get_burndown_data
from tests.conftest import make_issue, make_board, make_sprint


@patch("routers.burndown.client")
def test_burndown_normal(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board(bid=1)]
    sprint = make_sprint(
        sid=10, name="Sprint 1", state="active",
        start="2026-06-01T00:00:00+00:00",
        end="2026-06-14T00:00:00+00:00",
    )
    mock_client.get_sprints.return_value = [sprint]
    mock_client.get_sprint_issues.return_value = [
        make_issue("Done", category="done", orig_s=5 * 3600, spent_s=5 * 3600),
        make_issue("In Progress", category="indeterminate", orig_s=3 * 3600, spent_s=0),
    ]

    result = get_burndown_data("PROJ")

    assert result["sprint"] == "Sprint 1"
    assert result["board_id"] == 1
    assert result["total_h"] == 8
    assert result["done_h"] == 5
    assert result["remaining_h"] == 3
    assert result["total_pts"] == 8  # alias of total_h
    assert result["done_pts"] == 5   # alias of done_h
    assert len(result["days"]) == 14  # 13 days + 1 = 14 entries
    assert len(result["ideal"]) == 14
    assert len(result["actual"]) == 14
    assert result["ideal"][0] == 8.0
    assert result["ideal"][-1] == 0.0


@patch("routers.burndown.client")
def test_burndown_story_points_shown_as_secondary(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board()]
    mock_client.get_sprints.return_value = [make_sprint()]
    mock_client.get_sprint_issues.return_value = [
        make_issue("Done", category="done", sp=5, orig_s=3600, spent_s=3600),
        make_issue("In Progress", category="indeterminate", sp=3, orig_s=3600, spent_s=0),
    ]

    result = get_burndown_data("PROJ")

    assert result["total_sp"] == 8
    assert result["done_sp"] == 5


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
def test_burndown_no_effort(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board()]
    mock_client.get_sprints.return_value = [make_sprint()]
    mock_client.get_sprint_issues.return_value = [
        make_issue("Done", category="done"),
        make_issue("In Progress", category="indeterminate"),
    ]

    result = get_burndown_data("PROJ")

    assert result["total_h"] == 0
    assert result["done_h"] == 0
    assert result["ideal"][0] == 0.0


@patch("routers.burndown.client")
def test_burndown_sprint_without_issues(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board()]
    mock_client.get_sprints.return_value = [make_sprint()]
    mock_client.get_sprint_issues.return_value = []

    result = get_burndown_data("PROJ")

    assert result["total_h"] == 0
    assert result["done_h"] == 0


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
    mock_client.get_sprint_issues.return_value = [make_issue("Done", category="done", orig_s=10 * 3600, spent_s=10 * 3600)]

    result = get_burndown_data("PROJ")

    assert len(result["days"]) == len(result["ideal"]) == len(result["actual"])
    assert len(result["days"]) == 11  # 10 days + 1


@patch("routers.burndown.client")
def test_burndown_explicit_board_id_used(mock_client):
    boards = [make_board(bid=1, name="Board own"), make_board(bid=2, name="Board shared")]
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = boards

    def get_sprints(board_id, state=None):
        if board_id == 2 and state == "active":
            return [make_sprint(sid=99, name="Sprint on board 2")]
        return []

    mock_client.get_sprints.side_effect = get_sprints
    mock_client.get_sprint_issues.return_value = []

    result = get_burndown_data("PROJ", board_id=2)

    assert result["board_id"] == 2
    assert result["sprint"] == "Sprint on board 2"


@patch("routers.burndown.client")
def test_burndown_explicit_sprint_id_used(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board(bid=1)]
    mock_client.get_sprints.return_value = [
        make_sprint(sid=1, name="Old sprint", state="closed"),
        make_sprint(sid=2, name="Picked sprint", state="closed"),
    ]
    mock_client.get_sprint_issues.return_value = []

    result = get_burndown_data("PROJ", sprint_id=2)

    assert result["sprint"] == "Picked sprint"


@patch("routers.burndown.client")
def test_burndown_unknown_sprint_id_returns_empty(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board(bid=1)]
    mock_client.get_sprints.return_value = [make_sprint(sid=1, name="Only sprint")]

    result = get_burndown_data("PROJ", sprint_id=999)

    assert result["sprint"] is None
