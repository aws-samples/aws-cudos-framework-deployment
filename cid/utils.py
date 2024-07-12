import os
import sys
import copy
import math
import inspect
import logging
import platform
import datetime
from typing import Any, Dict
from functools import lru_cache as cache
from collections.abc import Iterable

import requests
import questionary
from boto3.session import Session
from botocore.exceptions import NoCredentialsError, CredentialRetrievalError, NoRegionError, ProfileNotFound

from cid.exceptions import CidCritical

logger = logging.getLogger(__name__)

params = {} # parameters from command line
_all_yes = False # parameters from command line

PYPI_URL = "https://pypi.org/pypi/cid-cmd/json"

def get_latest_tool_version():
    res_json = {}
    try:
        r = requests.get(PYPI_URL,timeout=3)
        r.raise_for_status()
        res_json = r.json()
    except requests.exceptions as exec:
        logger.debug(exec, exc_info=True)
    finally:
        return res_json.get("info", {}).get("version", "UNDEFINED")

@cache(maxsize=None)
def isatty():
    """ return True if executed in a Terminal that allows user input """
    if exec_env()['terminal'] == 'gitbash': # We cannot trust isatty on Git Bash on Windows
        return True
    return sys.__stdin__.isatty()

@cache(maxsize=None)
def exec_env():
    """ return os, shell and terminal
    supported environments: lambda, cloudsell, macos terminals, windows/cmd, windows/powershell, windows/gitbash
    """
    terminal = 'unknown'
    shell = 'unknown'
    os_ = platform.system()
    if os.environ.get('AWS_EXECUTION_ENV', '').startswith('AWS_Lambda'):
        terminal = 'lambda'
        shell = 'lambda'
    elif os.environ.get('AWS_EXECUTION_ENV', '') == 'CloudShell':
        terminal = 'cloudshell'
        shell = 'cloudshell'
    elif os.environ.get('SHELL', '').endswith('bash.exe'): # gitbash
        terminal = 'gitbash'
        shell = 'bash'
    elif os.environ.get('TERM_PROGRAM', ''):  # macos
        terminal = os.environ.get('TERM_PROGRAM', '')
        shell = os.environ.get('SHELL', '')
    elif os.environ.get('COMSPEC', '').endswith('cmd.exe'): # cmd
        terminal = 'cmd'
        shell = 'cmd'
    elif os.environ.get('PSMODULEPATH', ''): # powershell
        terminal = 'powershell'
        shell = 'powershell'
    return {'os': os_, 'shell': shell, 'terminal': terminal}


def intersection(a: Iterable, b: Iterable) -> Iterable:
    return sorted(set(a).intersection(b))

def difference(a: Iterable, b: Iterable) -> Iterable:
    return sorted(list(set(a).difference(b)))

def get_aws_region() -> str:
    return get_boto_session().region_name

def get_boto_session(**kwargs) -> Session:
    """
    Initiates boto's session object
    :param region: region name
    :param args: arguments
    :return: Boto3 Client
    """
    try:
        session = Session(**kwargs)
        logger.info('Boto3 session created')
        logger.debug(session)
        if not session.region_name:
            raise NoRegionError
        return session
    except (NoCredentialsError, CredentialRetrievalError):
        print('Error: unable to initialize session, please check your AWS credentials, exiting')
        exit(1)
    except NoRegionError:
        logger.info('No AWS region set, defaulting to us-east-1')
        kwargs.update({'region_name': 'us-east-1'})
        return get_boto_session(**kwargs)
    except ProfileNotFound as e:
        logger.critical(e)
        exit(1)
    except Exception as e:
        logger.debug(e, exc_info=True)
        raise

def get_boto_client(service_name, **kwargs):
    """
    Initiates boto's client object
    :param service_name: service name
    :param region: region name
    :param args: arguments
    :return: Boto3 Client
    """
    try:
        session = get_boto_session(**kwargs)
        return session.client(service_name)
    except (NoCredentialsError, CredentialRetrievalError):
        raise CidCritical('Error: unable to initialize boto client, please check your AWS credentials, exiting')
    except Exception as e:
        logger.debug(e, exc_info=True)
        raise


def cid_print(value, **kwargs) -> None:
    ''' Print AND log
    ex:
        violets, roses = 'violets', 'roses'
        cid_print(f'{roses} are <BOLD><RED>red<END>, {violets} are <BLUE><UNDERLINE>blue<END>')

    '''
    colors = {
        'PURPLE': '\033[95m',
        'CYAN': '\033[96m',
        'GREY': '\033[90m',
        'DARKCYAN': '\033[36m',
        'BLUE': '\033[94m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'RED': '\033[91m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m',
        'END': '\033[0m',
    }

    msg = str(value)
    log_msg = str(msg)
    for col, val in colors.items():
        msg = msg.replace(f'<{col}>', val)
        log_msg = log_msg.replace(f'<{col}>', '')
    try:
        mod = inspect.getmodule(inspect.stack()[1][0])
        name = mod.__name__ if mod else __name__
        logging.getLogger(name).debug(log_msg)
    except Exception as exc:
        logger.debug('cid_print: {exc}')
    print(msg, **kwargs)


def set_parameters(parameters: dict, all_yes: bool=None) -> None:
    for k, v in parameters.items():
        params[k.replace('_', '-')] = v

    if all_yes != None:
        global _all_yes
        _all_yes = all_yes

def get_parameters():
    return dict(params)


def get_yesno_parameter(param_name, message, default=None, break_on_ctrl_c=True):
    logger.debug(f'getting param {param_name}')
    param_name = param_name.replace('_', '-')
    mapping = {True: True, False:False, 'yes': True, 'no': False}
    if param_name in params and params.get(param_name) != None:
        return mapping[params.get(param_name)]
    if param_name in params and params.get(param_name) == None:
        unset_parameter(param_name)
    if default != None:
        default = 'yes' if mapping[default] else 'no'
    res = get_parameter(param_name, message=message, choices=['yes', 'no'], default=default, break_on_ctrl_c=break_on_ctrl_c)
    params[param_name] = (res == 'yes')
    return params[param_name]


def get_parameter(param_name, message, choices=None, default=None, none_as_disabled=False, template_variables={}, break_on_ctrl_c=True):
    """
    Check if parameters are provided in the command line and if not, ask user 

    :param message: text message for user
    :param choices: a list or dict for choice. None for text entry. Keys and Values must be strings.
    :param default: a default text template
    :param none_as_disabled: if True and choices is a dict, all choices with None as a value will be disabled
    :param template_variables: a dict with varibles for template
    :param break_on_ctrl_c: if True, exit() if user pressed CTRL+C

    :returns: a value choosed by user or provided in command line    
    """
    logger.debug(f'getting param {param_name}')
    param_name = param_name.replace('_', '-')
    if params.get(param_name):
        value = params[param_name]
        logger.info(f'Using {param_name}={value}, from parameters')
        if isinstance(value, str) and template_variables:
            try:
                value = value.format(**template_variables)
            except KeyError:
                pass
        return value

    if choices is not None:
        if 'yes' in choices and _all_yes:
            return 'yes'
        if isinstance(choices, dict):
            _choices = []
            for key, value in choices.items():
                _choices.append(
                    questionary.Choice(
                        title=key,
                        value=value,
                        disabled=True if (none_as_disabled and value is None) else False,
                    )
                )
                choices = _choices

        print()
        if not isatty():
            raise Exception(f'Please set parameter {param_name}. Unable to request user in environment={exec_env()}')
        result = questionary.select(
            message=f'[{param_name}] {message}:',
            choices=choices,
            default=default,
        ).ask()
    else: # it is a text entry
        if isinstance(default, str) and template_variables:
            print(template_variables)
            default=default.format(**template_variables)
        print()
        if not isatty():
            raise Exception(f'Please set parameter {param_name}. Unable to request user in environment={exec_env()}')
        result = questionary.text(
            message=f'[{param_name}] {message}:' ,
            default=default or '',
        ).ask()
        if isinstance(result, str) and template_variables:
            result = result.format(**template_variables)
    if (break_on_ctrl_c and result is None):
        exit(1)
    logger.info(f"(Use \033[1m --{param_name} '{result}'\033[0m next time you run this)")
    params[param_name] = result
    return result

def unset_parameter(param_name):
    param_name = param_name.replace('_', '-')
    if param_name in params:
        value = params[param_name]
        del params[param_name]
        logger.info(f'Cleared {param_name}={value}, from parameters')


def ago(time):
    """ Calculate a '3 hours ago' type string from a python datetime.
    credits: https://gist.github.com/tonyblundell/2652369
    """
    units = {
        'days': lambda diff: diff.days,
        'hours': lambda diff: diff.seconds / 3600,
        'minutes': lambda diff: diff.seconds % 3600 / 60,
    }
    diff = datetime.datetime.now().replace(tzinfo=time.tzinfo) - time
    for unit in units:
        dur = math.floor(units[unit](diff)) # Run the lambda function to get a duration
        if dur > 0:
            unit = unit[:-dur] if dur == 1 else unit # De-pluralize if duration is 1 ('1 day' vs '2 days')
            return '%s %s ago' % (dur, unit)
    return 'just now'


class IsolatedParameters:
    """A context manager to run something in isolated set of parameters"""
    def __enter__(self):
        self.backup = copy.deepcopy(params)

    def __exit__(self, exc_type, exc_value, traceback):
        global params
        params = self.backup

def merge_objects(obj1, obj2, depth=2):
    """ merging objects with a depth

    unit tests: cid/test/python/test_merge.py
    """
    if isinstance(obj1, dict) and isinstance(obj2, dict):
        result = obj1.copy()
        for key, value in obj2.items():
            if depth > 0 and key in result and isinstance(result[key], (dict, list)) and isinstance(value, (dict, list)):
                result[key] = merge_objects(result[key], value, depth - 1)
            else:
                result[key] = value
        return result
    elif isinstance(obj1, list) and isinstance(obj2, list):
        return obj1 + obj2
    else:
        return obj2  # If types don't match or if one of them is not a dict or list, prefer the second object.
