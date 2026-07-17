from status_category import categorize


def test_new_is_todo():
    assert categorize({"statusCategory": {"key": "new"}}) == "todo"


def test_indeterminate_is_in_progress():
    assert categorize({"statusCategory": {"key": "indeterminate"}}) == "in_progress"


def test_done_is_done():
    assert categorize({"statusCategory": {"key": "done"}}) == "done"


def test_unknown_key_defaults_to_in_progress():
    assert categorize({"statusCategory": {"key": "weird"}}) == "in_progress"


def test_missing_status_category_defaults_to_in_progress():
    assert categorize({"name": "Listo"}) == "in_progress"


def test_empty_dict_defaults_to_in_progress():
    assert categorize({}) == "in_progress"


def test_none_defaults_to_in_progress():
    assert categorize(None) == "in_progress"
