#!/usr/bin/env bash
set -euo pipefail

awslocal s3 mb s3://image-service-bucket 2>/dev/null || true
awslocal dynamodb create-table \
  --table-name images \
  --attribute-definitions AttributeName=image_id,AttributeType=S \
  --key-schema AttributeName=image_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST 2>/dev/null || true

echo "LocalStack resources are ready."
