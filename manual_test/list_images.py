from app.handler import lambda_handler

event = {
    "httpMethod": "GET",
    "path": "/images",
    "queryStringParameters": {
        "user_id": "abhinav",
        "content_type": "image/jpeg"
    }
}

response = lambda_handler(event, None)

print("Status:", response["statusCode"])
print("Body:", response["body"])