import base64
import json
import os

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['S3_BUCKET'] = 'image-service-bucket'
os.environ['DDB_TABLE'] = 'images'
os.environ.pop('AWS_ENDPOINT_URL', None)

import boto3
import pytest
from moto import mock_aws

from app.handler import lambda_handler


@pytest.fixture(autouse=True)
def aws_env():
    with mock_aws():
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='image-service-bucket')
        ddb = boto3.client('dynamodb', region_name='us-east-1')
        ddb.create_table(
            TableName='images',
            AttributeDefinitions=[{'AttributeName': 'image_id', 'AttributeType': 'S'}],
            KeySchema=[{'AttributeName': 'image_id', 'KeyType': 'HASH'}],
            BillingMode='PAY_PER_REQUEST',
        )
        yield


def invoke(method, path, body=None, query=None):
    event = {
        'httpMethod': method,
        'path': path,
        'queryStringParameters': query,
    }
    if body is not None:
        event['body'] = json.dumps(body)
    return lambda_handler(event, None)


def sample_payload(user_id='u1', content_type='image/png', filename='a.png'):
    return {
        'filename': filename,
        'content_type': content_type,
        'user_id': user_id,
        'image_base64': base64.b64encode(b'fake-image-bytes').decode('ascii'),
        'metadata': {'caption': 'hello', 'camera': 'phone'},
    }


def test_upload_success():
    resp = invoke('POST', '/images', sample_payload())
    assert resp['statusCode'] == 201
    body = json.loads(resp['body'])
    assert body['filename'] == 'a.png'
    assert body['user_id'] == 'u1'


def test_upload_missing_required_field():
    payload = sample_payload()
    payload.pop('user_id')
    resp = invoke('POST', '/images', payload)
    assert resp['statusCode'] == 400


def test_upload_invalid_base64():
    payload = sample_payload()
    payload['image_base64'] = 'not-valid@@@'
    resp = invoke('POST', '/images', payload)
    assert resp['statusCode'] == 400


def test_upload_rejects_non_image_content_type():
    resp = invoke('POST', '/images', sample_payload(content_type='text/plain'))
    assert resp['statusCode'] == 400


def test_list_with_two_filters():
    invoke('POST', '/images', sample_payload('u1', 'image/png', 'one.png'))
    invoke('POST', '/images', sample_payload('u2', 'image/jpeg', 'two.jpg'))
    invoke('POST', '/images', sample_payload('u1', 'image/jpeg', 'three.jpg'))

    resp = invoke('GET', '/images', query={'user_id': 'u1', 'content_type': 'image/jpeg'})
    assert resp['statusCode'] == 200
    items = json.loads(resp['body'])['items']
    assert len(items) == 1
    assert items[0]['filename'] == 'three.jpg'


def test_get_returns_presigned_url():
    created = json.loads(invoke('POST', '/images', sample_payload())['body'])
    resp = invoke('GET', '/images/{}'.format(created['image_id']))
    assert resp['statusCode'] == 200
    assert 'download_url' in json.loads(resp['body'])


def test_get_missing_image():
    resp = invoke('GET', '/images/missing')
    assert resp['statusCode'] == 404


def test_delete_success_and_then_404():
    created = json.loads(invoke('POST', '/images', sample_payload())['body'])
    image_id = created['image_id']

    resp = invoke('DELETE', '/images/{}'.format(image_id))
    assert resp['statusCode'] == 204

    resp = invoke('GET', '/images/{}'.format(image_id))
    assert resp['statusCode'] == 404


def test_delete_missing_image():
    resp = invoke('DELETE', '/images/missing')
    assert resp['statusCode'] == 404


def test_unknown_route():
    resp = invoke('GET', '/unknown')
    assert resp['statusCode'] == 404
