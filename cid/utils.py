import os
import sys
import logging
from collections.abc import Iterable
from typing import Dict

from boto3.session import Session
import questionary
from botocore.exceptions import NoCredentialsError, CredentialRetrievalError, NoRegionError, ProfileNotFound

logger = logging.getLogger(__name__)

params = {} # parameters from command line
_all_yes = False # parameters from command line


def isatty():
    return sys.__stdin__.isatty()

def exec_env():
    if os.environ.get('AWS_EXECUTION_ENV', '').startswith('AWS_Lambda'):
        return 'lambda'
    else:
        return 'unknown'


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
        logger.debug(e, stack_info=True)
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
        print('Error: unable to initialize boto client, please check your AWS credentials, exiting')
        exit(1)
    except Exception as e:
        logger.debug(e, stack_info=True)
        raise

def set_parameters(parameters: dict, all_yes: bool=None) -> None:
    for k, v in parameters.items():
        params[k.replace('_', '-')] = v

    if all_yes != None:
        global _all_yes
        _all_yes = all_yes

def is_unattendent_mode() -> bool:
    return _all_yes

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
        if isinstance(value, str):
            value = value.format(**template_variables)
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
        if isinstance(default, str):
            default=default.format(**template_variables)
        print()
        if not isatty():
            raise Exception(f'Please set parameter {param_name}. Unable to request user in environment={exec_env()}')
        result = questionary.text(
            message=f'[{param_name}] {message}:' ,
            default=default or '',
        ).ask()
        if isinstance(result, str):
            result = result.format(**template_variables)
    if (break_on_ctrl_c and result is None):
        exit(1)
    logger.info(f"(Use \033[1m --{param_name} '{result}'\033[0m next time you run this)")
    params[param_name] = result
    return result

def unset_parameter(param_name):
    param_name = param_name.replace('_', '-')
    if params.get(param_name):
        value = params[param_name]
        del params[param_name]
        logger.info(f'Cleared {param_name}={value}, from parameters')


def extract_cur_bucket_parameters(s3_path: str) -> Dict[str, str]:
    partitions = {
        "managed_by_cfn": ["source_account_id", "cur_name_1", "cur_name_2", "year", "month"],
        "manual":         ["year", "month"],
    }
    
    data = {}
    if s3_path.startswith('s3://'):
        s3_path = s3_path[len('s3://'):]
    if s3_path.endswith('/'):
        s3_path = s3_path[:-1]
    parts = s3_path.split('/')
    data['Bucket'] = parts[0]
    if len(parts[1:]) == 1:  # most likely it is created by CFN or similar
        data['Partitions'] = partitions['managed_by_cfn']
    elif len(parts) > 3 and parts[-1] == parts[-2]:  # most likely it is manual CUR
        data['Partitions'] = partitions['manual']
    else:
        raise Exception(f'CUR BucketPath={parts[0]} format is not recognized. It must be s3://(bucket)/cur or s3://{bucket}/{curprefix}/{curname}/{curname} ')
    data['Partitions'] = [{"Name": p, "Type": "string"} for p in data['Partitions']]
    data['Path'] = '/'.join(parts[1:])
    data['Folder'] = parts[-1] if len(parts) > 1 else ''
    data['Folder'] = data['Folder'].replace('-', '_').lower()  # this is used for a Glue table name that will be managed by crawler
    
    return data