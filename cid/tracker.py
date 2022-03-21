import requests
import json
import logging

logger = logging.getLogger(__name__)


def track(account_id: str, dashboard_id: str, operation: str):
    action = {'deploy': 'created', 'update': 'updated', 'delete': 'deleted'}.get(operation, None)
    method = {'created':'PUT', 'updated':'PATCH', 'deleted': 'DELETE'}.get(action, None)
    if not method:
        logger.debug(f"This will not fail the deployment. Logging action {action} is not supported. This issue will be ignored")
        return
    http = urllib3.PoolManager()
    endpoint = 'https://okakvoavfg.execute-api.eu-west-1.amazonaws.com/'
    payload = {
        'dashboard_id': dashboard_id,
        'account_id': self.awsIdentity.get('Account'),
        action + '_via': 'CID',
    }
    try:
        res = http.request(
            method=method,
            url=endpoint,
            body=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        if res.status != 200:
            logger.debug(f"This will not fail the deployment. There has been an issue logging action {action}  for dashboard {dashboard_id} and account {account_id}, server did not respond with a 200 response,actual  status: {res.status}, response data {res.data.decode('utf-8')}. This issue will be ignored")
    except Exception as e:
        logger.debug(f"Issue logging action {action} for dashboard {dashboard_id}, due to a urllib3 exception {str(e)}. This issue will be ignored")
