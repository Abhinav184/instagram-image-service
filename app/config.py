import os

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET = os.getenv('S3_BUCKET', 'image-service-bucket')
DDB_TABLE = os.getenv('DDB_TABLE', 'images')
AWS_ENDPOINT_URL = os.getenv('AWS_ENDPOINT_URL') or None
MAX_IMAGE_BYTES = int(os.getenv('MAX_IMAGE_BYTES', str(5 * 1024 * 1024)))
