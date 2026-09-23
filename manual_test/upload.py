import base64
import json

from app.handler import lambda_handler


# Read actual image and convert it to Base64
with open("test-image.jpg", "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")


event = {
    "httpMethod": "POST",
    "path": "/images",
    "body": json.dumps({
        "filename": "test-image.jpg",
        "content_type": "image/jpeg",
        "user_id": "abhinav",
        "image_base64": image_base64,
        "metadata": {
            "caption": "LocalStack test image",
            "location": "Bengaluru"
        }
    })
}

response = lambda_handler(event, None)

print("Status:", response["statusCode"])
print("Body:", response["body"])