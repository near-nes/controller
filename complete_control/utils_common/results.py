import datetime, random, string


def make_trial_id(
    timestamp_str: str | None = None,
    label: str = "trial",
    suffix_len: int = 4,
):
    """Return a readable, time-sortable trial ID."""
    timestamp_str = timestamp_str or datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=suffix_len)
    )
    return f"{timestamp_str}_{suffix}-{label}"
