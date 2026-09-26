from services.hackathon_api import ask_gemini

text, remaining = ask_gemini(
    "Reply with only: PYTHON API WORKING"
)

print(text)
print("Requests remaining:", remaining)