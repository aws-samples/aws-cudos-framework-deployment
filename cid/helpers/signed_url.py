""" Returns a presigned URL generated from your AWS CLI credentials.
"""
import json
from urllib import parse

import requests
from cid.exceptions import CidError

def get_signed_url(session, destination="https://console.aws.amazon.com/", duration=43200):
    """ Returns a presigned URL generated from your AWS CLI credentials.

    :session: boto3 sesson
    :destination: destination url
    :duration: DurationSeconds max 43200s = 12h

    credits -> https://gist.github.com/ottokruse/1c0f79d51cdaf82a3885f9b532df1ce5
    """
    creds = session.get_credentials()
    if not creds:
        raise CidError("Failed to get credentials. Please make sure you have AWS session credentials in this shell.")
    url_credentials = {
        'sessionId': creds.access_key,
        'sessionKey': creds.secret_key,
        'sessionToken': creds.token,   
    }
    request_parameters = "?Action=getSigninToken"
    request_parameters += f"&DurationSeconds={duration}"
    request_parameters += "&Session=" + parse.quote_plus(json.dumps(url_credentials))
    request_url = "https://signin.aws.amazon.com/federation" + request_parameters

    response = requests.get(request_url, timeout=300)
    if not response.status_code == 200:
        raise CidError("Failed to get federation token.")

    signin_token = response.json()
    request_parameters = "?Action=login"
    request_parameters += "&Destination=" + parse.quote_plus(destination)
    request_parameters += "&SigninToken=" + signin_token["SigninToken"]
    request_parameters += "&Issuer=" + parse.quote_plus("https://example.com")
    request_url = "https://signin.aws.amazon.com/federation" + request_parameters
    return request_url
