import boto3
from .config import AWS_ENDPOINT_URL, AWS_REGION


def client(service_name):
    kwargs = {'region_name': AWS_REGION}
    if AWS_ENDPOINT_URL:
        kwargs['endpoint_url'] = AWS_ENDPOINT_URL
        kwargs['aws_access_key_id'] = os.getenv('AWS_ACCESS_KEY_ID', 'test')
        kwargs['aws_secret_access_key'] = os.getenv('AWS_SECRET_ACCESS_KEY', 'test')
    return boto3.client(service_name, **kwargs)


import os
