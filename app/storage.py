from .aws import client
from .config import S3_BUCKET


def put_image_bytes(key, data, content_type):
    client('s3').put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
    )


def delete_image_object(key):
    client('s3').delete_object(Bucket=S3_BUCKET, Key=key)


def presigned_download_url(key, expires=900):
    return client('s3').generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': key},
        ExpiresIn=expires,
    )
