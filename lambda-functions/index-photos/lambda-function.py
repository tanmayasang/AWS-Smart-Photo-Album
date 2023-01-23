'''
    LF1: Triggered by S3 bucket whenever a new image is uploaded
'''

import requests
from requests_aws4auth import AWS4Auth
import boto3
import datetime
import json
import logging
import os

elastic_search_host = os.environ.get('ELASTIC_SEARCH_HOST')
region = os.environ.get('REGION')
elastic_search_index = os.environ.get('ELASTIC_SEARCH_INDEX')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def try_ex(func):
    try:
        return func()
    except KeyError:
        return None

def get_photo_labels(bucket, photo):
    client = boto3.client('rekognition', region_name=region)
    response = client.detect_labels(Image={'S3Object':{'Bucket': bucket, 'Name': photo}}, MaxLabels=10)
    labels = try_ex(lambda: response['Labels'])
    all_labels = [l['Name'] for l in labels]
    return all_labels

def put_to_es(index, type, new_doc):
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)
    
    endpoint = '{}/{}/{}'.format(elastic_search_host, index, type)
    headers = {'Content-Type': 'application/json'}
    r = requests.post(endpoint, auth=awsauth, data=new_doc, headers=headers)
    print(r.content)

def get_s3_metadata(bucket, photo):
    s3 = boto3.client('s3')
    metadata = s3.head_object(Bucket=bucket, Key=photo)
    logger.debug('Getting metadata: ')
    logger.debug(metadata)
    return metadata['Metadata']['x-amz-meta-customlabels'] if metadata['Metadata']['x-amz-meta-customlabels'] is not None else ''

def lambda_handler(event, context):
    logger.debug('LF is invoked by S3')
    logger.debug(event)

    # Extract new img from the S3 event
    s3obj = try_ex(lambda: event['Records'])
    if not s3obj:
        return {
        'statusCode': 500,
        'errorMsg': 'Event message does not follow S3 JSON structure ver 2.1'
    }

    for obj in s3obj:
        bucket = try_ex(lambda: obj['s3']['bucket']['name'])
        photo = try_ex(lambda: obj['s3']['object']['key'])

        # Get all labels
        logger.debug('Getting label for  %s::%s' % (bucket, photo))
        labels = get_photo_labels(bucket, photo)
        logger.debug('Labels for %s::%s are %s' % (bucket, photo, labels))

        # Get custom labels
        custom_labels = get_s3_metadata(bucket, photo)
        custom_labels = custom_labels.split(',') if custom_labels is not None else []

        labels = labels + custom_labels
        logger.debug('Combined Labels: ')
        logger.debug(labels)

        # Index the photo
        doc = {
            'objectKey': photo,
            'bucket': bucket,
            'createdTimestamp': datetime.datetime.now().strftime('%Y-%d-%m-T%H:%M:%S'),
            'labels': labels
        }
        put_to_es(elastic_search_index, 'photo', json.dumps(doc))

    return {
        'statusCode': 200,
        'body': doc
    }