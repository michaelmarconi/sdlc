from booklog.log import add, books


def test_added_books_are_listed_in_order(tmp_path):
    log = tmp_path / "log"
    add(log, "Middlemarch", "George Eliot")
    add(log, "Beloved", "Toni Morrison")
    assert books(log) == [("Middlemarch", "George Eliot"), ("Beloved", "Toni Morrison")]


def test_a_missing_log_has_no_books(tmp_path):
    assert books(tmp_path / "none") == []
