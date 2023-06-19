import re
import random
from datetime import datetime, timedelta


def get_random_time_from_range(time_range):
    """Return random time in format hh:mm within provided time range"""
    if not time_range:
        # return default random time between 02:00 and 04:59
        return f"{random.randrange(2, 5):02d}:{random.randrange(0, 60):02d}", None

    random_time = ""
    try:
        time_re = re.match(r'^(([01]\d|2[0-3]):([0-5]\d)|24:00)-(([01]\d|2[0-3]):([0-5]\d)|24:00)$', time_range)
        time_from = datetime.strptime(time_re.group(1), '%H:%M')
        time_to = datetime.strptime(time_re.group(4), '%H:%M')
        if time_to < time_from:
            time_to += timedelta(days=1)
        time_diff_sec = (time_to - time_from).total_seconds()
        random_seconds = random.randrange(0, int(time_diff_sec))
        random_time = (time_from + timedelta(seconds=random_seconds)).strftime('%H:%M')
    except Exception as e:
        return "", e

    return random_time, None