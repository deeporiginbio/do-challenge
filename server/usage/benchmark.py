import random

import requests
api = "http://localhost:5000/api"

url = f"{api}/benchmark"
headers = {"Content-Type": "application/json", "x-token": "7PUv5IaUK0ty8H7iF_wAo3pwa94xPQ85LTwMpS4h1FU="}
body = {
    "challenge_name": "DO2025",
    "indexes": [random.choice(range(500000)) for i in range(2000)]
}

if __name__ == "__main__":
    response = requests.post(url, json=body, headers=headers)

    print("Response:", response.json())
