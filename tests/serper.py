import requests, json

api_key = "dae9dbfe92891624116876b484dbbfcccb52ddbe"

print("Key len:", len(api_key))

resp = requests.post(
    "https://google.serper.dev/search",
    headers={
        "X-API-KEY": api_key.strip(),
        "Content-Type": "application/json",
    },
    json={"q": "test", "num": 1},
)
print(resp.status_code)
print(resp.text)
