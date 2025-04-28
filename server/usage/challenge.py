import time
import requests

api = "http://localhost:5000/api"
HEADERS = {"Content-Type": "application/json", "X-API-KEY": "DeepOriginAdmin"}

TEAM_NAMES = ["DeepThought1", "DeepThought2"]


def create_challenge():
    url = f"{api}/challenges"
    body = {"title": "DO2025", "description": "Test"}
    response = requests.post(url, json=body, headers=HEADERS, verify=False)

    response.raise_for_status()
    return response.json()["challenge_id"]


def create_team(name):
    url = f"{api}/teams"
    body = {"name": name}
    response = requests.post(url, json=body, headers=HEADERS, verify=False)

    response.raise_for_status()
    return response.json()["team_id"], response.json()["password"]


def create_task(team_id, challenge_id):
    url = f"{api}/tasks"
    body = {"team_id": team_id, "challenge_id": challenge_id}
    response = requests.post(url, json=body, headers=HEADERS, verify=False)

    response.raise_for_status()
    return response.json()["task_id"]


def login(team_name, password):
    url = f"{api}/login"
    body = {"name": team_name, "password": password}
    response = requests.post(url, json=body, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    return response.json()["secret_key"]


if __name__ == "__main__":
    challenge_id = create_challenge()
    secrets = []

    for team_name in TEAM_NAMES:
        team_id, team_pass = create_team(team_name)
        time.sleep(3)  # Increased delay

        # Retry mechanism for create_task
        for attempt in range(3):
            try:
                create_task(team_id, challenge_id)
                break
            except requests.exceptions.ConnectionError:
                wait_time = 2 ** attempt
                print(f"Task creation failed. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        else:
            print("Failed after 3 retries.")

        time.sleep(3)

        team_secret_key = login(team_name, team_pass)
        secrets.append(
            f"Team: {team_name}\nID: {team_id}\nPassword: {team_pass}\nSecret Key: {team_secret_key}\n{'*' * 50}\n")

        time.sleep(2)

    with open("secrets.txt", "w") as f:
        f.writelines(secrets)

    print("Secrets saved to secrets.txt")
