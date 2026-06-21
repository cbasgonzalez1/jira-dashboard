from unittest.mock import patch
from routers.velocity import get_velocity_data
from tests.conftest import make_issue, make_board, make_sprint


def _sprint_issues(done_sp=5, total_sp=8):
    return [
        make_issue("Done", sp=done_sp),
        make_issue("In Progress", sp=total_sp - done_sp),
    ]


@patch("routers.velocity.client")
def test_velocity_normal(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board()]
    mock_client.get_sprints.side_effect = lambda board_id, state=None: {
        "closed": [
            make_sprint(1, "Sprint 1", "closed"),
            make_sprint(2, "Sprint 2", "closed"),
            make_sprint(3, "Sprint 3", "closed"),
        ],
        "active": [make_sprint(4, "Sprint 4", "active")],
    }.get(state, [])
    mock_client.get_sprint_issues.return_value = _sprint_issues(done_sp=5, total_sp=8)

    result = get_velocity_data("PROJ")

    assert result["project"] == "PROJ"
    assert len(result["sprints"]) == 4
    closed = [s for s in result["sprints"] if s["state"] == "closed"]
    assert len(closed) == 3
    assert all(s["completed"] == 5 for s in closed)
    assert result["avg_velocity"] == 5


@patch("routers.velocity.client")
def test_velocity_no_boards(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = []

    result = get_velocity_data("PROJ")

    assert result["sprints"] == []
    assert result["avg_velocity"] == 0


@patch("routers.velocity.client")
def test_velocity_no_closed_sprints(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board()]
    mock_client.get_sprints.side_effect = lambda board_id, state=None: (
        [] if state == "closed" else [make_sprint(1, state="active")]
    )
    mock_client.get_sprint_issues.return_value = []

    result = get_velocity_data("PROJ")

    assert result["avg_velocity"] == 0
    assert any(s["state"] == "active" for s in result["sprints"])


@patch("routers.velocity.client")
def test_velocity_zero_story_points(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board()]
    mock_client.get_sprints.side_effect = lambda board_id, state=None: {
        "closed": [make_sprint(1, "Sprint 1", "closed")],
        "active": [],
    }.get(state, [])
    mock_client.get_sprint_issues.return_value = [make_issue("Done", sp=None)]

    result = get_velocity_data("PROJ")

    assert result["avg_velocity"] == 0
    assert result["sprints"][0]["completed"] == 0


@patch("routers.velocity.client")
def test_velocity_sprint_window_respected(mock_client):
    """Only the last VELOCITY_SPRINT_WINDOW closed sprints should be used."""
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board()]
    # 5 closed sprints available; window=3 means only last 3 are used
    mock_client.get_sprints.side_effect = lambda board_id, state=None: {
        "closed": [make_sprint(i, f"Sprint {i}", "closed") for i in range(1, 6)],
        "active": [],
    }.get(state, [])
    mock_client.get_sprint_issues.return_value = []

    result = get_velocity_data("PROJ")

    closed = [s for s in result["sprints"] if s["state"] == "closed"]
    assert len(closed) == 3


@patch("routers.velocity.client")
def test_velocity_api_error(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.side_effect = Exception("connection error")

    result = get_velocity_data("PROJ")

    assert result["sprints"] == []
    assert result["avg_velocity"] == 0
