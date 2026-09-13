# Image Service Coding Assignment

A small serverless image service implemented for AWS API Gateway + Lambda + S3 + DynamoDB.

## Architecture

- API Gateway exposes the REST endpoints.
- Lambda contains the service/API logic.
- S3 stores image bytes.
- DynamoDB stores image metadata.
- LocalStack provides S3 and DynamoDB locally.

## API

### 1. Upload image + metadata

`POST /images`

Request body:

```json
{
  "filename": "photo.png",
  "content_type": "image/png",
  "user_id": "user-123",
  "image_base64": "<base64 encoded image bytes>",
  "metadata": {
    "caption": "sample",
    "location": "Bengaluru"
  }
}
```

Returns `201 Created` with the stored metadata.

### 2. List images

`GET /images`

Supported filters:

- `user_id`
- `content_type`
- `filename`

Also supports `limit` and `last_key` for pagination.

Example:

```bash
GET /images?user_id=user-123&content_type=image/png
```

### 3. View/download image

`GET /images/{image_id}`

Returns metadata plus a short-lived S3 presigned `download_url`.

### 4. Delete image

`DELETE /images/{image_id}`

Deletes both the S3 object and the DynamoDB record.

## Local development

### Prerequisites

- Python 3.7+
- Docker / Docker Compose

### Start LocalStack

```bash
docker compose up -d
```

The init script automatically creates:

- S3 bucket: `image-service-bucket`
- DynamoDB table: `images`

### Create Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For direct local calls against LocalStack:

```bash
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_REGION=us-east-1
```

## Run unit tests

```bash
pytest -q
```

The unit tests use `moto` so they run quickly and do not require Docker.

## Example local Lambda invocation

```bash
python - <<'PY'
import base64, json
from app.handler import lambda_handler

event = {
  "httpMethod": "POST",
  "path": "/images",
  "body": json.dumps({
    "filename": "sample.png",
    "content_type": "image/png",
    "user_id": "user-1",
    "image_base64": base64.b64encode(b"demo-image").decode(),
    "metadata": {"caption": "demo"}
  })
}
print(lambda_handler(event, None))
PY
```

## AWS deployment

`template.yaml` contains an AWS SAM definition for API Gateway, Lambda, S3 and DynamoDB.

Typical deployment:

```bash
sam build
sam deploy --guided
```

## Design notes / trade-offs

1. Images are stored in S3 while DynamoDB stores only metadata and the S3 key.
2. Downloads use presigned S3 URLs so Lambda does not proxy the image bytes.
3. Upload size is capped at 5 MB for this exercise. For production-scale uploads, the preferred design is a two-step API that returns a presigned S3 upload URL, avoiding API Gateway/Lambda payload limits.
4. The list endpoint supports three filters. This exercise uses DynamoDB Scan + FilterExpression to keep the implementation compact. At high scale, use GSIs/access-pattern-specific keys instead of scans.
5. If DynamoDB persistence fails after S3 upload, the code attempts a compensating S3 delete to reduce orphaned objects.
6. The API uses pagination (`limit` + `last_key`) to avoid unbounded list responses.

## Test coverage

Tests cover:

- Successful upload
- Required-field validation
- Invalid base64
- Invalid MIME type
- Listing with multiple filters
- View/download URL
- Missing image handling
- Successful delete
- Missing delete target
- Unknown routes
