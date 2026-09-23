import json
from app.handler import lambda_handler

# Get an existing image
list_response = lambda_handler({
    "httpMethod": "GET",
    "path": "/images",
    "queryStringParameters": {
        "user_id": "abhinav",
        "content_type": "image/jpeg"
    }
}, None)

items = json.loads(list_response["body"])["items"]

if not items:
    print("No images found to delete")
else:
    image_id = items[0]["image_id"]

    # Delete image
    response = lambda_handler({
        "httpMethod": "DELETE",
        "path": f"/images/{image_id}"
    }, None)

    print("Image ID:", image_id)
    print("Status:", response["statusCode"])
    print("Body:", response["body"])