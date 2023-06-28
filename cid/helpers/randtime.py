import re
import hashlib
from datetime import datetime, timedelta

def random_generator(hashable_string, maximum_value):
    """Provide random integer number based on input parameter"""
    return int.from_bytes(bytes.fromhex(hashlib.md5(bytes(hashable_string, "utf-8")).hexdigest()[:16]), 'little', signed=True)%int(maximum_value)

def get_random_time_from_range(hashable_string, input_time):
    """
    In case that input time is in format hh:mm, just return it back.
    When input time is time range hh:mm-hh:mm, then return random time in format hh:mm within provided time range
    """
    random_time = ""

    timerange = input_time.strip().split('-')

    if len(timerange) == 1:
        try:
            random_time = datetime.strptime(input_time.strip(), '%H:%M').strftime('%H:%M')
        except Exception as exc:
            raise ValueError(f'Invalid time range "{input_time}": {str(exc)}')
        return random_time
    elif len(timerange) == 2:
        try:
            time_from = datetime.strptime(timerange[0].strip(), '%H:%M')
            time_to = datetime.strptime(timerange[1].strip(), '%H:%M')
            if time_to < time_from:
                time_to += timedelta(days=1)
            time_diff_sec = (time_to - time_from).total_seconds()
            random_time = (time_from + timedelta(seconds=random_generator(hashable_string, time_diff_sec))).strftime('%H:%M')
        except Exception as exc:
            raise ValueError(f'Invalid time range "{input_time}": {str(exc)}')
        return random_time
    else:
        raise ValueError(f'Invalid time range "{input_time}". Please provide timerange in format hh:mm or hh:mm-hh:mm')