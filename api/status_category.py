CATEGORY_KEY_MAP = {
    "new": "todo",
    "indeterminate": "in_progress",
    "done": "done",
}


def categorize(status_field: dict) -> str:
    """Classify a Jira status using its built-in statusCategory.key.

    statusCategory.key is stable and language-independent ("new",
    "indeterminate", "done"), unlike status names which vary per
    custom workflow and per locale.
    """
    key = ((status_field or {}).get("statusCategory") or {}).get("key")
    return CATEGORY_KEY_MAP.get(key, "in_progress")
