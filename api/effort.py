def extract_effort(fields: dict, sp_field: str) -> dict:
    """Extract committed/spent effort for an issue, in both hours and story points.

    Hours (timetracking) is the primary unit for this Jira instance — most
    teams estimate and log work in hours, not story points. Story points are
    returned alongside as a secondary, often-empty metric.

    This is a pure extractor: it does not decide whether the issue counts as
    "done" — callers combine `committed_sp` / `spent_h` with
    status_category.categorize() to build their own committed/done totals.
    """
    tt = fields.get("timetracking") or {}
    committed_s = tt.get("originalEstimateSeconds") or fields.get("timeoriginalestimate") or 0
    spent_s = tt.get("timeSpentSeconds") or fields.get("timespent") or 0

    committed_sp = fields.get(sp_field) or fields.get("customfield_11934") or 0

    return {
        "committed_h": round(committed_s / 3600, 2),
        "spent_h": round(spent_s / 3600, 2),
        "committed_sp": committed_sp,
    }
