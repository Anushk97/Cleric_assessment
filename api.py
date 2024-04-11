import requests

payload = {
  "question": "what are the design decisions?",
  "documents": [
    "https://llm-bot-pficsoahpa-uc.a.run.app/static/call_log_20240314_104111.txt",
    "https://llm-bot-pficsoahpa-uc.a.run.app/static/call_log_20240315_104111.txt"
  ],
  "autoApprove": True
}

response = requests.post('http://127.0.0.1:8000/submit_and_retrieve', json=payload)
#response = requests.post('https://llm-bot-pficsoahpa-uc.a.run.app/submit_and_retrieve', json=payload)

if response.status_code == 200:
    print(response.json())
else:
    print("Failed to send request:", response.status_code)
