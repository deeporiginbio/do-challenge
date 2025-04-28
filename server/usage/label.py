import requests

url = "http://localhost:5000/api/get_labels"
headers = {"Content-Type": "application/json", "x-token": "BGXyzjC7def09M3JKz6lz-0DndILcJRk2WMsF88Nov4="}

body = {
    "challenge_name": "DO2025",
    "indexes": [i for i in range(10000)]
}

if __name__ == "__main__":
    response = requests.post(url, json=body, headers=headers)

    print("Response:", response.json())

    available_tokens_url = "http://localhost:5000/api/available_tokens"
    available_tokens_response = requests.get(available_tokens_url, headers=headers)
    print("Response:", available_tokens_response.json())
