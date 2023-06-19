import boto3
from tzlocal.windows_tz import win_tz, tz_win
from tzlocal import get_localzone_name

from cid.utils import exec_env

MAPPING_REGION_2_TIMEZONE = {
    "us-east-1": "America/New_York",
    "us-east-2": "America/New_York",
    "us-west-1": "America/Los_Angeles",
    "us-west-2": "America/Los_Angeles",
    "af-south-1": "Africa/Blantyre",
    "ap-east-1": "Asia/Hong_Kong",
    "ap-south-1": "Asia/Kolkata",
    "ap-southeast-3": "Asia/Jakarta",
    "ap-south-1": "Asia/Kolkata",
    "ap-southeast-4": "Australia/Melbourne",
    "ap-northeast-3": "Asia/Tokyo",
    "ap-northeast-2": "Asia/Seoul",
    "ap-southeast-1": "Asia/Singapore",
    "ap-southeast-2": "Australia/Sydney",
    "ap-northeast-1": "Asia/Tokyo",
    "ca-central-1": "America/Toronto",
    "eu-central-1": "Europe/Berlin",
    "eu-west-1": "Europe/Dublin",
    "eu-west-2": "Europe/London",
    "eu-south-1": "Europe/Rome",
    "eu-west-3": "Europe/Paris",
    "eu-south-2": "Europe/Madrid",
    "eu-north-1": "Europe/Stockholm",
    "eu-central-2": "Europe/Zurich",
    "me-south-1": "Asia/Riyadh",
    "me-central-1": "Asia/Dubai",
    "sa-east-1": "America/Sao_Paulo",
    "us-gov-east-1": "US/Eastern",
    "us-gov-west-1": "US/Pacific",
}


def get_timezone_from_aws_region(region):
    """ Get Timezone from AWS region. """
    return MAPPING_REGION_2_TIMEZONE.get(region)


def get_default_timezone():
    """ Get timzone best guess from Shell or from Region. """
    if exec_env()['terminal'] not in ('cloudshell', 'lambda'):
        region = boto3.session.Session().region_name
        return get_timezone_from_aws_region(region)
    else:
        return get_localzone_name()


def get_all_timezones():
    """Get all zones"""
    # zoneinfo is not working with 3.7, 3.8
    return sorted(list(win_tz.values()))

def get_execution_timezone(proposed_tz):
    """Get timezone from provided parameter or best guess from shell or from region"""
    if proposed_tz and proposed_tz in tz_win:
        return proposed_tz

    if exec_env()['terminal'] not in ('lambda'):
        region = boto3.session.Session().region_name
        return get_timezone_from_aws_region(region)
    else:
        return get_localzone_name()