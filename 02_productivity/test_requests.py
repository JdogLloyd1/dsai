import requests

url = "https://httpbin.org/post"
payload = {"name": "test"}

r = requests.post(url, json=payload)
print(r.status_code)
print(r.json())
