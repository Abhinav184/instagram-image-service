from decimal import Decimal
from boto3.dynamodb.conditions import Attr
import boto3
from .config import AWS_ENDPOINT_URL, AWS_REGION, DDB_TABLE


def _resource():
    kwargs = {'region_name': AWS_REGION}
    if AWS_ENDPOINT_URL:
        kwargs.update({
            'endpoint_url': AWS_ENDPOINT_URL,
            'aws_access_key_id': 'test',
            'aws_secret_access_key': 'test',
        })
    return boto3.resource('dynamodb', **kwargs)


def table():
    return _resource().Table(DDB_TABLE)


def put_image(item):
    table().put_item(Item=item, ConditionExpression='attribute_not_exists(image_id)')


def get_image(image_id):
    return table().get_item(Key={'image_id': image_id}).get('Item')


def delete_image(image_id):
    resp = table().delete_item(
        Key={'image_id': image_id},
        ReturnValues='ALL_OLD'
    )
    return resp.get('Attributes')


def list_images(user_id=None, content_type=None, filename=None, limit=50, last_key=None):
    limit = max(1, min(int(limit), 100))
    filters = []
    if user_id:
        filters.append(Attr('user_id').eq(user_id))
    if content_type:
        filters.append(Attr('content_type').eq(content_type))
    if filename:
        filters.append(Attr('filename').contains(filename))

    kwargs = {'Limit': limit}
    if last_key:
        kwargs['ExclusiveStartKey'] = {'image_id': last_key}
    if filters:
        expression = filters[0]
        for f in filters[1:]:
            expression = expression & f
        kwargs['FilterExpression'] = expression

    resp = table().scan(**kwargs)
    return resp.get('Items', []), resp.get('LastEvaluatedKey')
