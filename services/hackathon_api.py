import os
import json
import requests


API_URL = "https://hackathon-api-new-152590733511.northamerica-northeast2.run.app/api/generate"


def ask_gemini(prompt, response_schema=None):

    payload = {
        "contents": prompt
    }

    if response_schema is not None:
        payload["response_schema"] = response_schema

    response = requests.post(
        API_URL,
        headers={
            "X-API-Key": os.environ["HACKATHON_API_KEY"]
        },
        json=payload,
        timeout=90
    )

    response.raise_for_status()

    data = response.json()

    text = data["text"]

    if response_schema is not None:
        text = json.loads(text)

    return text, data["requests_remaining"]