''' Helper functions for dataset schedules
'''
import hashlib
from datetime import datetime, timedelta

def pseudo_random_generator(hashable_string: str, maximum: int=100) -> int:
    """Gernerate a pseudo random integer number, but the same for any given hashable_string identifier """
    hash_hex = hashlib.md5(bytes(hashable_string, "utf-8")).hexdigest()[:16] # nosec B303, B324 - not used for security
    bigint_value = int.from_bytes(bytes.fromhex(hash_hex), 'little', signed=True)
    return bigint_value % int(maximum)

def get_random_time_from_range(hashable_string, time_range):
    """ Generate a random time from a given range
    In case that input time is in format hh:mm, just return it back.
    When input time is time range hh:mm-hh:mm, then return random time in format hh:mm within provided time range
    """
    items = time_range.strip().split('-')

    if len(items) == 1:
        try:
            return datetime.strptime(time_range.strip(), '%H:%M').strftime('%H:%M')
        except Exception as exc:
            raise ValueError(f'Invalid time range "{time_range}": {str(exc)}') from exc
    elif len(items) == 2:
        try:
            time_from = datetime.strptime(items[0].strip(), '%H:%M')
            time_to = datetime.strptime(items[1].strip(), '%H:%M')
            if time_to < time_from:
                time_to += timedelta(days=1)
            time_diff_sec = (time_to - time_from).total_seconds()
            return (time_from + timedelta(seconds=pseudo_random_generator(hashable_string, time_diff_sec))).strftime('%H:%M')
        except Exception as exc:
            raise ValueError(f'Invalid time range "{time_range}": {str(exc)}') from exc
    else:
        raise ValueError(f'Invalid time range "{time_range}". Please provide timerange in format hh:mm or hh:mm-hh:mm')
