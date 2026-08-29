import requests

url = "http://localhost:4000/api/v1/auth/login"
payload = {
    "email": "testuser@mindmesh.com",
    "password": "Password123!"
}

try:
    res = requests.post(url, json=payload)
    print("STATUS CODE:", res.status_code)
    print("RESPONSE JSON/TEXT:", res.text)
except Exception as e:
    print("ERROR:", str(e))
