import base64
import hashlib
import hmac
import random
import string
from datetime import datetime, timezone

from bson import ObjectId
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest, NotFound, Forbidden
from werkzeug.security import generate_password_hash

from app.models.models import Team


class TeamsRepository:
    def __init__(self, db):
        self.collection = db.get_collection("teams")

    def create_team(self, team_name: str):
        try:
            password, password_hash = self._generate_password()
            secret_key = self.generate_token(password)
            team_data = Team(
                name=team_name,
                password=password_hash,
                secret_key=secret_key,
                created_at=datetime.now(timezone.utc)
            ).model_dump(by_alias=True, exclude=["id"])
            result = self.collection.insert_one(team_data)
            return str(result.inserted_id), str(password)
        except ValidationError as e:
            raise BadRequest(f"Invalid data, please check the fields and try again. {e}")

    def get_team_by_id(self, team_id: str):
        team_data = self.collection.find_one({"_id": ObjectId(team_id)}, {'secret_key': 0, 'password': 0})
        if not team_data:
            raise NotFound("Team not found")
        return Team(**team_data)

    def get_team_by_secret_key(self, secret_key: str):
        team_data = self.collection.find_one({"secret_key": secret_key})
        if not team_data:
            raise Forbidden("Invalid secret key")
        return Team(**team_data)

    def get_team_by_name(self, team_name: str):
        team_data = self.collection.find_one({"name": team_name})
        return Team(**team_data) if team_data else None

    def get_all_teams(self, filter_by_name=None):
        query = {} if not filter_by_name else {"name": filter_by_name}
        documents = self.collection.find(query, {'secret_key': 0, 'password': 0})
        teams = []
        if documents:
            for doc in documents:
                teams.append(Team(**doc))
            return teams
        return []

    def update_team(self, team_id: str, update_data: dict):
        result = self.collection.update_one({"_id": ObjectId(team_id)}, {"$set": update_data})
        if result.modified_count == 0:
            raise NotFound("Team not found")

        return result.modified_count

    def delete_team(self, team_id: str):
        result = self.collection.delete_one({"_id": ObjectId(team_id)})
        if result.deleted_count == 0:
            raise NotFound("Team not found")

        return result.deleted_count

    def _generate_password(self):
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        return password, generate_password_hash(password)

    def generate_token(self, password: str, salt: str = "some_salt"):
        key = hmac.new(salt.encode(), password.encode(), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(key).decode()
