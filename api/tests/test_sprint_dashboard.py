import asyncio
from unittest.mock import patch
from routers.sprint_dashboard import dashboard_data, list_projects, list_boards, list_sprints
from tests.conftest import make_issue, make_sprint, make_board


def run(coro):
    return asyncio.run(coro)


SPRINT = make_sprint(
    sid=42, name="Sprint X", state="active",
    start="2026-06-01T00:00:00+00:00",
    end="2026-06-14T00:00:00+00:00",
)


@patch("routers.sprint_dashboard.client")
def test_data_normal(mock_client):
    mock_client.get_sprints.return_value = [SPRINT]
    mock_client.get_board_sprint_issues.return_value = [
        make_issue("Done", assignee_name="alice", sp=5, orig_s=3600, spent_s=3600),
        make_issue("In Progress", assignee_name="bob", sp=3, orig_s=7200, rem_s=3600, spent_s=3600),
    ]

    result = run(dashboard_data(board_id=1, sprint_id=42))

    assert result["sprint"]["id"] == 42
    assert result["kpis"]["total_issues"] == 2
    assert result["kpis"]["done_issues"] == 1
    assert result["kpis"]["done_sp"] == 5
    assert result["kpis"]["total_sp"] == 8
    assert result["kpis"]["team_size"] == 2
    assert len(result["by_person"]) == 2
    assert len(result["by_project"]) == 1


@patch("routers.sprint_dashboard.client")
def test_data_sprint_not_found(mock_client):
    mock_client.get_sprints.return_value = [SPRINT]

    result = run(dashboard_data(board_id=1, sprint_id=999))

    assert "error" in result
    assert result["error"] == "Sprint not found"


@patch("routers.sprint_dashboard.client")
def test_data_no_issues(mock_client):
    mock_client.get_sprints.return_value = [SPRINT]
    mock_client.get_board_sprint_issues.return_value = []

    result = run(dashboard_data(board_id=1, sprint_id=42))

    assert result["kpis"]["total_issues"] == 0
    assert result["kpis"]["done_issues"] == 0
    assert result["kpis"]["team_size"] == 0
    assert result["by_person"] == []
    assert result["by_project"] == []


@patch("routers.sprint_dashboard.client")
def test_data_no_assignee(mock_client):
    mock_client.get_sprints.return_value = [SPRINT]
    mock_client.get_board_sprint_issues.return_value = [
        make_issue("In Progress", assignee_name=None, sp=3, rem_s=3600),
    ]

    result = run(dashboard_data(board_id=1, sprint_id=42))

    assert result["kpis"]["team_size"] == 0  # _unassigned not counted
    persons = {p["account_id"]: p for p in result["by_person"]}
    assert "_unassigned" in persons


@patch("routers.sprint_dashboard.client")
def test_data_no_time_tracking(mock_client):
    """Issue with empty timetracking dict should not raise."""
    mock_client.get_sprints.return_value = [SPRINT]
    issue = make_issue("In Progress", assignee_name="alice", sp=3)
    issue["fields"]["timetracking"] = {}
    issue["fields"]["timespent"] = None
    issue["fields"]["timeoriginalestimate"] = None
    mock_client.get_board_sprint_issues.return_value = [issue]

    result = run(dashboard_data(board_id=1, sprint_id=42))

    assert result["kpis"]["total_issues"] == 1
    assert result["kpis"]["deviation_pct"] == 0.0


@patch("routers.sprint_dashboard.client")
def test_data_zero_original_estimate_no_deviation(mock_client):
    """orig_s == 0 must not produce a deviation entry (division guard)."""
    mock_client.get_sprints.return_value = [SPRINT]
    mock_client.get_board_sprint_issues.return_value = [
        make_issue("Done", assignee_name="alice", sp=5, orig_s=0, spent_s=7200),
    ]

    result = run(dashboard_data(board_id=1, sprint_id=42))

    assert result["deviations"] == []


@patch("routers.sprint_dashboard.client")
def test_data_zero_team_size_capacity(mock_client):
    """team_size=0 (all unassigned) must not produce negative capacity."""
    mock_client.get_sprints.return_value = [SPRINT]
    mock_client.get_board_sprint_issues.return_value = [
        make_issue("In Progress", assignee_name=None, sp=3, rem_s=3600),
    ]

    result = run(dashboard_data(board_id=1, sprint_id=42))

    assert result["kpis"]["team_size"] == 0
    assert result["kpis"]["capacity_remaining_h"] == 0.0


@patch("routers.sprint_dashboard.client")
def test_data_deviation_only_above_threshold(mock_client):
    """Deviations only appear when |dev_pct| > 10."""
    mock_client.get_sprints.return_value = [SPRINT]
    mock_client.get_board_sprint_issues.return_value = [
        # 5% over — below threshold
        make_issue("Done", assignee_name="alice", key="PROJ-1", sp=5,
                   orig_s=3600, spent_s=3780),
        # 50% over — above threshold
        make_issue("Done", assignee_name="alice", key="PROJ-2", sp=5,
                   orig_s=3600, spent_s=5400),
    ]

    result = run(dashboard_data(board_id=1, sprint_id=42))

    assert len(result["deviations"]) == 1
    assert result["deviations"][0]["key"] == "PROJ-2"


@patch("routers.sprint_dashboard.client")
def test_data_custom_done_status_counted(mock_client):
    """'Listo'/'Resuelta' aren't in any hardcoded name list, but their
    statusCategory.key is 'done' — they must count as done, not in_progress."""
    mock_client.get_sprints.return_value = [SPRINT]
    mock_client.get_board_sprint_issues.return_value = [
        make_issue("Listo", category="done", assignee_name="alice", sp=5, orig_s=3600, spent_s=3600),
        make_issue("Resuelta", category="done", assignee_name="bob", sp=3, orig_s=3600, spent_s=3600),
    ]

    result = run(dashboard_data(board_id=1, sprint_id=42))

    assert result["kpis"]["done_issues"] == 2
    assert result["kpis"]["done_sp"] == 8


@patch("routers.sprint_dashboard.client")
def test_list_projects(mock_client):
    mock_client.get_all_projects.return_value = [
        {"key": "B", "name": "Beta"},
        {"key": "A", "name": "Alpha"},
    ]

    result = run(list_projects())

    assert result[0]["key"] == "A"
    assert result[1]["key"] == "B"


@patch("routers.sprint_dashboard.client")
def test_list_boards_by_project(mock_client):
    mock_client.get_boards.return_value = [make_board(1, "Board 1")]

    result = run(list_boards(project_key="PROJ"))

    assert len(result) == 1
    assert result[0]["id"] == 1


@patch("routers.sprint_dashboard.client")
def test_list_sprints_sorted(mock_client):
    mock_client.get_sprints.return_value = [
        make_sprint(3, "Old", "closed"),
        make_sprint(1, "Current", "active"),
        make_sprint(5, "Next", "future"),
    ]

    result = run(list_sprints(board_id=1))

    states = [s["state"] for s in result]
    assert states == ["active", "future", "closed"]
