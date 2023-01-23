'''
    LF2: Lambda proxy for API gateway to search photos based on user query
'''

import boto3
from requests_aws4auth import AWS4Auth
import json
import logging
import requests
import os

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

lex_bot_name = os.environ.get('LEX_BOT_NAME')
elastic_search_host = os.environ.get('ELASTIC_SEARCH_HOST')
elastic_search_region = os.environ.get('ELASTIC_SEARCH_REGION')
elastic_search_index = os.environ.get('ELASTIC_SEARCH_INDEX')

# For safe slot extraction
def try_ex(func):
    try:
        return func()
    except KeyError:
        return None

def lambda_handler(event, context):
    logger.debug('EVENT:')
    logger.debug(event)
    logger.debug(context)

    raw_query = try_ex(lambda: event['query'])
    logger.debug(event['query'])
    logger.debug(raw_query)
    if not raw_query:
        return {
            'statusCode': 400,
            'body': 'No query found in event'
        }

    # Use Lex to disambiguate query
    keywords = []
    client = boto3.client('lex-runtime')
    response = client.post_text(
        botName = lex_bot_name,
        botAlias = '$LATEST',
        userId = 'searchPhotosLambda',
        inputText = raw_query
    )
    
    logger.debug('LEX Response:')
    logger.debug(response)

    slots = try_ex(lambda: response['slots'])
    for _, v in slots.items():
        if v: # ignore empty slots
            keywords.append(v)

    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, elastic_search_region, 'es', session_token=credentials.token)

    query = '{}/{}/_search'.format(elastic_search_host, elastic_search_index)
    headers = {'Content-Type': 'application/json'}
    prepared_q = []
    for k in keywords:
        prepared_q.append({"match": {"labels": k}})
    q = {"query": {"bool": {"should": prepared_q}}}
    r = requests.post(query, auth=awsauth, headers=headers, data=json.dumps(q))
    data = json.loads(r.content.decode('utf-8'))
    
    logger.debug('Elastic Search Result')
    logger.debug(data)

    # Extract images
    all_photos = []
    prepend_url = 'https://s3.amazonaws.com'
    hits = try_ex(lambda: data['hits']['hits'])
    for h in hits:
        photo = {}
        obj_bucket = try_ex(lambda: h['_source']['bucket'])
        obj_key = try_ex(lambda: h['_source']['objectKey'])
        full_photo_path = '/'.join([prepend_url, obj_bucket, obj_key])
        photo['url'] = full_photo_path
        photo['labels'] = try_ex(lambda: h['_source']['labels'])
        all_photos.append(photo)

    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json"
        },
        'body': {'results': all_photos}
    }