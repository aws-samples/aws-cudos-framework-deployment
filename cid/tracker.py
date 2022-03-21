import requests
import json
import logging

logger = logging.getLogger(__name__)


def track(account_id: str, dashboard_id: str, operation: str):
    action = {
        'deploy': 'created',
        'update': 'updated',
        'delete': 'deleted'
    }.get(operation, None)
    if not action:
        logger.debug(f"This will not fail the deployment. Logging operation {operation} is not supported. This issue will be ignored")
        return    
    try:
        res = requests.request(
            method={
                'created': 'PUT', 
                'updated': 'PATCH', 
                'deleted': 'DELETE',
            }.get(action),
            url='https://okakvoavfg.execute-api.eu-west-1.amazonaws.com/',
            data={
                'dashboard_id': dashboard_id,
                'account_id': account_id,
                action + '_via': 'CID',
            },
            headers={'Content-Type': 'application/json'}
        )
        if res.status_code != 200:
            logger.debug(f"This will not fail the deployment. There has been an issue logging action {action}  for dashboard {dashboard_id} and account {account_id}, server did not respond with a 200 response,actual  status: {res.status_code}, response data {res.text}. This issue will be ignored")
    except Exception as e:
        logger.debug(f"Issue logging action {action} for dashboard {dashboard_id}, due to a urllib3 exception {str(e)}. This issue will be ignored")
