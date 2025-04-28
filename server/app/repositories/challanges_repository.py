import os
from datetime import datetime, timezone

import pymongo
from bson import ObjectId
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest, NotFound

from app.config.core import settings
from app.models.models import Challenge


class ChallengeRepository:
    def __init__(self, db):
        self.collection = db.get_collection("challenges")

    def create_challenge(self, title, description, initial_tokens, free_benchmarks):
        try:
            challenge_data = Challenge(
                title=title,
                description=description,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                initial_tokens=initial_tokens,
                free_benchmarks=free_benchmarks,
            ).model_dump(by_alias=True, exclude=["id"])

            os.makedirs(f"{settings.DATASETS_PATH}/{title}", exist_ok=True)
        except ValidationError as e:
            raise BadRequest(f"Invalid data, please check the fields and try again. {e}")

        try:
            result = self.collection.insert_one(challenge_data)
        except pymongo.errors.DuplicateKeyError as e:
            raise BadRequest(f"Challenge with title {title} already exists")

        return str(result.inserted_id)

    def get_challenge_by_id(self, challenge_id):
        document = self.collection.find_one({"_id": ObjectId(challenge_id)})
        if not document:
            raise NotFound("Challenge not found")
        return Challenge(**document)

    def get_challenge_by_name(self, challenge_name: str = "DO2025"):
        document = self.collection.find_one({"title": challenge_name})
        if not document:
            raise NotFound("Challenge not found")
        return Challenge(**document)

    def start_challenge(self, challenge_name: str):
        challenge = self.get_challenge_by_name(challenge_name)
        if challenge.start_time:
            raise BadRequest("Challenge already started")
        start_time = datetime.now(timezone.utc)
        update_data = {
            "start_time":start_time,
        }
        result = self.collection.update_one({"_id": ObjectId(challenge.id)}, {"$set": update_data})
        return start_time

    def end_challenge(self, challenge_name: str):
        challenge = self.get_challenge_by_name(challenge_name)
        if not challenge.start_time:
            raise BadRequest("Challenge not started")
        if challenge.end_time:
            raise BadRequest("Challenge already ended")
        end_time = datetime.now(timezone.utc)
        update_data = {
            "end_time": end_time,
        }
        result = self.collection.update_one({"_id": ObjectId(challenge.id)}, {"$set": update_data})
        return end_time

    def get_all_challenges(self):
        documents = self.collection.find({})
        challenges = []
        if documents:
            for doc in documents:
                challenges.append(Challenge(**doc))
            return challenges

        return []

    def update_challenge(self, challenge_id, update_data):
        update_data['updated_at'] = datetime.now(timezone.utc)
        result = self.collection.update_one({"_id": ObjectId(challenge_id)}, {"$set": update_data})
        if result.modified_count == 0:
            raise NotFound("Challenge not found")

        return result.modified_count

    def delete_challenge(self, challenge_id):
        result = self.collection.delete_one({"_id": ObjectId(challenge_id)})
        if result.deleted_count == 0:
            raise NotFound("Challenge not found")

        return result.deleted_count
