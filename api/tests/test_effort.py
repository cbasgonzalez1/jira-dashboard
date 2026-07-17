from effort import extract_effort


def test_hours_from_timetracking():
    fields = {
        "timetracking": {"originalEstimateSeconds": 14400, "timeSpentSeconds": 7200},
        "customfield_10002": None,
    }
    result = extract_effort(fields, "customfield_10002")
    assert result["committed_h"] == 4.0
    assert result["spent_h"] == 2.0
    assert result["committed_sp"] == 0


def test_hours_fallback_to_flat_fields_when_no_timetracking():
    fields = {
        "timeoriginalestimate": 28800,
        "timespent": 3600,
        "customfield_10002": None,
    }
    result = extract_effort(fields, "customfield_10002")
    assert result["committed_h"] == 8.0
    assert result["spent_h"] == 1.0


def test_story_points_primary_field():
    fields = {"customfield_10002": 5, "customfield_11934": None}
    result = extract_effort(fields, "customfield_10002")
    assert result["committed_sp"] == 5


def test_story_points_fallback_field():
    fields = {"customfield_10002": None, "customfield_11934": 3}
    result = extract_effort(fields, "customfield_10002")
    assert result["committed_sp"] == 3


def test_no_effort_data_at_all():
    result = extract_effort({}, "customfield_10002")
    assert result == {"committed_h": 0.0, "spent_h": 0.0, "committed_sp": 0}
