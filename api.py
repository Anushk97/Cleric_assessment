import requests

payload = {
  "question": "summarize this",
  "documents": [
    "https://txt2html.sourceforge.net/sample.txt",
    "https://www.michaelhorowitz.com/sample.hosts.file.txt"
  ],
  "autoApprove": True
}

#response = requests.post('http://127.0.0.1:8000/submit_and_retrieve', json=payload)
response = requests.post('https://llm-bot-pficsoahpa-uc.a.run.app/submit_and_retrieve', json=payload)

if response.status_code == 200:
    print(response.json())  # Assuming the response is in JSON format
else:
    print("Failed to send request:", response.status_code)
