import boto3

from botocore.exceptions import NoCredentialsError, CredentialRetrievalError, NoRegionError

import logging
logger = logging.getLogger(__name__)

def get_aws_region():
    return get_boto_session().region_name

def get_boto_session(**kwargs):
    """
    Initiates boto's session object
    :param region: region name
    :param args: arguments
    :return: Boto3 Client
    """
    try:
        session = boto3.session.Session(**kwargs)
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
    except:
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
    except:
        raise
