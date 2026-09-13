import base64
import json
import uuid
from datetime import datetime, timezone

from .config import MAX_IMAGE_BYTES
from .repository import put_image, get_image, delete_image, list_images
from .storage import put_image_bytes, delete_image_object, presigned_download_url


def _response(status, body):
    return {
        'statusCode': status,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body),
    }


def _json_body(event):
    raw = event.get('body') or '{}'
    if event.get('isBase64Encoded'):
        raw = base64.b64decode(raw).decode('utf-8')
    return json.loads(raw)


def _query(event):
    return event.get('queryStringParameters') or {}


def create_image(event):
    try:
        body = _json_body(event)
    except Exception:
        return _response(400, {'message': 'Invalid JSON body'})

    required = ['filename', 'content_type', 'user_id', 'image_base64']
    missing = [k for k in required if not body.get(k)]
    if missing:
        return _response(400, {'message': 'Missing required fields', 'fields': missing})

    if not str(body['content_type']).startswith('image/'):
        return _response(400, {'message': 'content_type must be an image/* MIME type'})

    try:
        image_bytes = base64.b64decode(body['image_base64'], validate=True)
    except Exception:
        return _response(400, {'message': 'image_base64 is invalid'})

    if not image_bytes:
        return _response(400, {'message': 'Image is empty'})
    if len(image_bytes) > MAX_IMAGE_BYTES:
        return _response(413, {'message': 'Image exceeds maximum upload size'})

    image_id = str(uuid.uuid4())
    s3_key = 'images/{}/{}'.format(image_id, body['filename'])
    created_at = datetime.now(timezone.utc).isoformat()

    item = {
        'image_id': image_id,
        'filename': body['filename'],
        'content_type': body['content_type'],
        'user_id': body['user_id'],
        's3_key': s3_key,
        'size_bytes': len(image_bytes),
        'created_at': created_at,
        'metadata': body.get('metadata') or {},
    }

    try:
        put_image_bytes(s3_key, image_bytes, body['content_type'])
        put_image(item)
    except Exception:
        # Compensating action: avoid leaving an orphaned S3 object if metadata persistence fails.
        try:
            delete_image_object(s3_key)
        except Exception:
            pass
        return _response(500, {'message': 'Failed to persist image'})

    return _response(201, item)


def list_all_images(event):
    q = _query(event)
    try:
        items, last_key = list_images(
            user_id=q.get('user_id'),
            content_type=q.get('content_type'),
            filename=q.get('filename'),
            limit=q.get('limit', 50),
            last_key=q.get('last_key'),
        )
    except ValueError:
        return _response(400, {'message': 'limit must be an integer'})

    return _response(200, {
        'items': items,
        'next_last_key': (last_key or {}).get('image_id'),
    })


def view_image(image_id):
    item = get_image(image_id)
    if not item:
        return _response(404, {'message': 'Image not found'})

    result = dict(item)
    result['download_url'] = presigned_download_url(item['s3_key'])
    return _response(200, result)


def remove_image(image_id):
    item = get_image(image_id)
    if not item:
        return _response(404, {'message': 'Image not found'})

    try:
        delete_image_object(item['s3_key'])
        delete_image(image_id)
    except Exception:
        return _response(500, {'message': 'Failed to delete image'})

    return _response(204, {})


def lambda_handler(event, context):
    method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
    path = event.get('path') or event.get('rawPath') or ''

    if method == 'POST' and path == '/images':
        return create_image(event)
    if method == 'GET' and path == '/images':
        return list_all_images(event)

    if path.startswith('/images/'):
        image_id = path.split('/')[-1]
        if method == 'GET':
            return view_image(image_id)
        if method == 'DELETE':
            return remove_image(image_id)

    return _response(404, {'message': 'Route not found'})
