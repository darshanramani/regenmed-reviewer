import os
import base64
import requests

API_URL = "https://hackathon-api-new-152590733511.northamerica-northeast2.run.app/api/generate"

image_path = "test_form.png"

with open(image_path, "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

payload = {
    "contents": {
        "text": "Identify what type of document this is.",
        "image_base64": image_base64
    }
}

response = requests.post(
    API_URL,
    headers={
        "X-API-Key": os.environ["HACKATHON_API_KEY"]
    },
    json=payload,
    timeout=90
)

print("Status code:", response.status_code)

if response.status_code == 200:
    print("SUCCESS")
    print(response.json())
else:
    print("IMAGE INPUT NOT SUPPORTED IN THIS FORMAT")
    print(response.text[:500])