from analyzer import count_error, most_common, logs_in_date


def test_count_error_counts_repeated_errors():
    logs = [
        "2026-10-20 09:13:45 ERROR Database connection timeout",
        "2026-10-20 09:16:10 INFO File uploaded",
        "2026-10-20 09:18:33 ERROR Database connection timeout",
        "2026-10-20 09:20:05 ERROR Invalid user token",
    ]

    result = count_error(logs)

    assert result == {"Database connection timeout": 2, "Invalid user token": 1}


def test_count_error_no_errors_returns_empty_dict():
    logs = [
        "2026-10-20 09:12:01 INFO User login successful",
        "2026-10-20 09:15:22 WARNING Disk usage at 85%",
    ]

    assert count_error(logs) == {}


def test_most_common_tie_broken_by_severity():
    error = {"error1": 1, "error2": 2, "error3": 2}
    severity = {"error1": 1, "error2": 2, "error3": 3}

    assert most_common(error, severity, 2) == [("error3", 2), ("error2", 2)]


def test_most_common_sorted_by_count():
    error = {"error1": 1, "error2": 2, "error3": 3}
    severity = {"error1": 1, "error2": 1, "error3": 1}

    assert most_common(error, severity, 3) == [
        ("error3", 3),
        ("error2", 2),
        ("error1", 1),
    ]


def test_most_common_returns_only_num():
    error = {"error1": 1, "error2": 2, "error3": 3}
    severity = {"error1": 1, "error2": 1, "error3": 1}

    assert most_common(error, severity, 2) == [("error3", 3), ("error2", 2)]


def test_logs_in_date_returns_matching_lines():
    logs = [
        "2026-10-22 09:13:45 ERROR Database connection timeout",
        "2026-10-20 09:16:10 INFO File uploaded",
        "2026-10-20 09:18:33 ERROR Database connection timeout",
        "2026-10-22 09:20:05 ERROR Invalid user token",
    ]
    wanted_date = "2026-10-20"

    assert logs_in_date(logs, wanted_date) == [
        ["2026-10-20", "09:16:10", "INFO", "File uploaded"],
        ["2026-10-20", "09:18:33", "ERROR", "Database connection timeout"],
    ]


def test_logs_in_date_no_match_returns_empty():
    logs = [
        "2026-10-22 09:13:45 ERROR Database connection timeout",
        "2026-10-20 09:16:10 INFO File uploaded",
        "2026-10-20 09:18:33 ERROR Database connection timeout",
        "2026-10-22 09:20:05 ERROR Invalid user token",
    ]
    wanted_date = "2026-06-20"

    assert logs_in_date(logs, wanted_date) == []
