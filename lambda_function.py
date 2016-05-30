from base64 import b64decode
import boto3
import json
import logging
import requests
from urlparse import parse_qs

ENCRYPTED_EXPECTED_TOKEN = "CiDyexpbL9wdCxI5ILidoKjFi1RJbSs9oujWqJ7AUV/CURKfAQEBAgB48nsaWy/cHQsSOSC4naCoxYtUSW0rPaLo1qiewFFfwlEAAAB2MHQGCSqGSIb3DQEHBqBnMGUCAQAwYAYJKoZIhvcNAQcBMB4GCWCGSAFlAwQBLjARBAwu3zMGw3HxkXi8K7MCARCAM2HbhK067ygTJDmNA4JGZuuIN4fiP0NkswvrjHt72Mixe2FiwP4ABixK/PAKRI6jOj6T+g==" # Enter the base-64 encoded, encrypted Slack command token (CiphertextBlob)

ENCRYPTED_PAGERDUTY_TOKEN = "CiDyexpbL9wdCxI5ILidoKjFi1RJbSs9oujWqJ7AUV/CURKbAQEBAgB48nsaWy/cHQsSOSC4naCoxYtUSW0rPaLo1qiewFFfwlEAAAByMHAGCSqGSIb3DQEHBqBjMGECAQAwXAYJKoZIhvcNAQcBMB4GCWCGSAFlAwQBLjARBAxAIHcF5pvoY0JWELkCARCAL8IQtg9JGNPZCiP0jWXdOAvbxq87NgRGLtVQ/CzU5QONxrlH0ba4P+gWnshBaTdw"

kms = boto3.client('kms')

expected_token = kms.decrypt(CiphertextBlob = b64decode(ENCRYPTED_EXPECTED_TOKEN))['Plaintext']
pagerduty_token = kms.decrypt(CiphertextBlob = b64decode(ENCRYPTED_PAGERDUTY_TOKEN))['Plaintext']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    req_body = event['body']
    params = parse_qs(req_body)
    token = params['token'][0]
    if token != expected_token:
        logger.error("Request token (%s) does not match exptected", token)
        raise Exception("Invalid request token")

    user = params['user_name'][0]
    command = params['command'][0]
    channel = params['channel_name'][0]

    response = requests.get("https://eero.pagerduty.com/api/v1/escalation_policies/on_call", headers={"Authorization": "Token token=%s" % pagerduty_token})
    data = response.json()

    oncall_people = ["%s: %s" % (d['name'], d['on_call'][0]['user']['name']) for d in data.get('escalation_policies', [])]
    return {"text": "\n".join(oncall_people)}
