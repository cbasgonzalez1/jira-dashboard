from unittest.mock import patch
from routers.velocity import get_velocity_data
from tests.conftest import make_issue, make_board, make_sprint


def _sprint_issues_hours(done_h=5, total_h=8):
    """One done issue (spent == original, counts as completed) and one
    in-progress issue, so committed == total_h and completed == done_h."""
    done_s = done_h * 3600
    remaining_s = (total_h - done_h) * 3600
    return [
        make_issue("Done", category="done", orig_s=done_s, spent_s=done_s),
        make_issue("In Progress", category="indeterminate", orig_s=remaining_s, spent_s=0),
    ]


@patch("routers.velocity.client")
def test_velocity_normal(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board(bid=1)]
    mock_client.get_sprints.side_effect = lambda board_id, state=None: {
        "closed": [
            make_sprint(1, "Sprint 1", "closed"),
            make_sprint(2, "Sprint 2", "closed"),
            make_sprint(3, "Sprint 3", "closed"),
        ],
        "active": [make_sprint(4, "Sprint 4", "active")],
    }.get(state, [])
    mock_client.get_board_sprint_issues.return_value = _sprint_issues_hours(done_h=5, total_h=8)

    result = get_velocity_data("PROJ")

    assert result["project"] == "PROJ"
    assert result["board_id"] == 1
    assert len(result["sprints"]) == 4
    closed = [s for s in result["sprints"] if s["state"] == "closed"]
    assert len(closed) == 3
    assert all(s["completed"] == 5 for s in closed)
    assert all(s["committed"] == 8 for s in closed)
    assert result["avg_velocity"] == 5


@patch("routers.velocity.client")
def test_velocity_story_points_shown_as_secondary(mock_client):
    """When a sprint does have story points, they ride along as *_sp fields
    without replacing hours as the primary committed/completed metric."""
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board(bid=1)]
    mock_client.get_sprints.side_effect = lambda board_id, state=None: {
        "closed": [make_sprint(1, "Sprint 1", "closed")],
        "active": [],
    }.get(state, [])
    mock_client.get_board_sprint_issues.return_value = [
        make_issue("Done", category="done", orig_s=3600, spent_s=3600, sp=5),
        make_issue("In Progress", category="indeterminate", orig_s=3600, spent_s=0, sp=3),
    ]

    result = get_velocity_data("PROJ")

    sprint = result["sprints"][0]
    assert sprint["completed"] == 1  # 1h spent on the done issue
    assert sprint["completed_sp"] == 5
    assert sprint["committed_sp"] == 8
    assert result["avg_velocity_sp"] == 5


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
    mock_client.get_board_sprint_issues.return_value = []

    result = get_velocity_data("PROJ")

    assert result["avg_velocity"] == 0
    assert any(s["state"] == "active" for s in result["sprints"])


@patch("routers.velocity.client")
def test_velocity_zero_effort(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = [make_board()]
    mock_client.get_sprints.side_effect = lambda board_id, state=None: {
        "closed": [make_sprint(1, "Sprint 1", "closed")],
        "active": [],
    }.get(state, [])
    mock_client.get_board_sprint_issues.return_value = [make_issue("Done", category="done", sp=None)]

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
    mock_client.get_board_sprint_issues.return_value = []

    result = get_velocity_data("PROJ")

    closed = [s for s in result["sprints"] if s["state"] == "closed"]
    assert len(closed) == 3


@patch("routers.velocity.client")
def test_velocity_explicit_board_id_used(mock_client):
    boards = [make_board(bid=1, name="Board own"), make_board(bid=2, name="Board shared")]
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = boards
    mock_client.get_sprints.side_effect = lambda board_id, state=None: (
        [make_sprint(10, "Sprint on board 2", "active")] if board_id == 2 and state == "active" else []
    )
    mock_client.get_board_sprint_issues.return_value = []

    result = get_velocity_data("PROJ", board_id=2)

    assert result["board_id"] == 2
    assert result["sprints"][0]["name"] == "Sprint on board 2"


@patch("routers.velocity.client")
def test_velocity_unknown_board_id_falls_back_to_first(mock_client):
    boards = [make_board(bid=1)]
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.return_value = boards
    mock_client.get_sprints.return_value = []
    mock_client.get_board_sprint_issues.return_value = []

    result = get_velocity_data("PROJ", board_id=999)

    assert result["board_id"] == 1


@patch("routers.velocity.client")
def test_velocity_api_error(mock_client):
    mock_client.get_story_points_field.return_value = "customfield_10002"
    mock_client.get_boards.side_effect = Exception("connection error")

    result = get_velocity_data("PROJ")

    assert result["sprints"] == []
    assert result["avg_velocity"] == 0
