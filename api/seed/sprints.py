from datetime import datetime, timedelta

# Velocity (story points completed) for historical sprints
HISTORICAL_VELOCITIES = [
    {"name_suffix": "Sprint 1", "velocity": 34, "weeks_ago": 12},
    {"name_suffix": "Sprint 2", "velocity": 41, "weeks_ago": 10},
    {"name_suffix": "Sprint 3", "velocity": 38, "weeks_ago": 8},
]

ACTIVE_SPRINT = {"name_suffix": "Sprint 4", "weeks_ago": 1}
FUTURE_SPRINT = {"name_suffix": "Sprint 5"}


def sprint_dates(weeks_ago: int, duration_weeks: int = 2):
    now = datetime.utcnow()
    start = now - timedelta(weeks=weeks_ago + duration_weeks)
    end = start + timedelta(weeks=duration_weeks)
    return (
        start.strftime("%Y-%m-%dT%H:%M:%S.000+0000"),
        end.strftime("%Y-%m-%dT%H:%M:%S.000+0000"),
    )


def active_sprint_dates(duration_weeks: int = 2):
    now = datetime.utcnow()
    start = now - timedelta(weeks=1)
    end = start + timedelta(weeks=duration_weeks)
    return (
        start.strftime("%Y-%m-%dT%H:%M:%S.000+0000"),
        end.strftime("%Y-%m-%dT%H:%M:%S.000+0000"),
    )
