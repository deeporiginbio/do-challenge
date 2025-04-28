import json
from datetime import datetime, timezone

import pymongo
from bson import ObjectId
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest, NotFound

from app.models.models import Task
from .challanges_repository import ChallengeRepository
from .teams_repository import TeamsRepository
from ..config.core import settings


class TaskRepository:
    def __init__(self, db):
        self.db = db
        self.collection = db.get_collection("tasks")
        self.challenge_repository = ChallengeRepository(db)
        self.teams_repository = TeamsRepository(db)

    def create_task(self, team_id: str, challenge_id: str, id_mappings: dict=None):
        challenge = self.challenge_repository.get_challenge_by_id(challenge_id)
        team = self.teams_repository.get_team_by_id(team_id)
        try:
            task_data = Task(
                team_id=team.id,
                challenge_id=challenge.id,
                status='pending',
                available_tokens=challenge.initial_tokens,
                available_benchmarks=challenge.free_benchmarks,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                requested_correct_ids=[],
            ).model_dump(by_alias=True, exclude=["id"])

        except ValidationError as e:
            raise BadRequest(f"Invalid data, please check the fields and try again. {e}")

        try :
            result = self.collection.insert_one(task_data)
        except pymongo.errors.DuplicateKeyError as e:
            raise BadRequest(f"Task already exists")

        return str(result.inserted_id)

    @staticmethod
    def _frozen_sorting_key(team_id: str):
        def key(task):
            if task.team_id == team_id:
                return -task.best_benchmark_score if task.best_benchmark_score else 0
            return -task.frozen_benchmark_score if task.frozen_benchmark_score else 0
        return key

    def reset_task(self, team_id: str):
        task = self.get_task_by_team_and_challenge(team_id, settings.CHALLENGE_NAME)
        update_data = {
            "status": "pending",
            "available_tokens": self.challenge_repository.get_challenge_by_id(task.challenge_id).initial_tokens,
            "available_benchmarks": self.challenge_repository.get_challenge_by_id(task.challenge_id).free_benchmarks,
            "benchmarks": [],
            "best_benchmark_score": None,
            "frozen_benchmark_score": None,
            "last_benchmark_hash": None,
            "requested_correct_ids": [],
            "updated_at": datetime.now(timezone.utc)
        }
        result = self.collection.update_one({"_id": ObjectId(task.id)}, {"$set": update_data})
        if result.matched_count == 0:
            raise NotFound("Task not found")
        return result.modified_count


    def get_all(self, team_secret_key, challenge_id=None, ranked=False):
        query = {"challenge_id": challenge_id} if challenge_id else {}
        documents = self.collection.find(query, {'requested_correct_ids': 0})

        team = self.teams_repository.get_team_by_secret_key(team_secret_key)
        tasks = [Task(**doc) for doc in documents]

        if ranked:
            if team.name != "Admin":
                if tasks[0].status == "frozen":
                    tasks = sorted(tasks, key=self._frozen_sorting_key(team.id))
                else:
                    tasks = sorted(tasks, key=lambda task: -task.best_benchmark_score if task.best_benchmark_score else 0)
                for ind, task in enumerate(tasks, start=1):
                    if task.status == "frozen" and task.team_id != team.id:
                        if task.frozen_benchmark_score:
                            task.best_benchmark_score = task.frozen_benchmark_score
                        else:
                            task.best_benchmark_score = None
                    if task.team_id == team.id:
                        task.team_name = team.name
                    else:
                        task.team_name = f"Team {ind}"
            else:
                tasks = sorted(tasks, key=lambda task: -task.best_benchmark_score if task.best_benchmark_score else 0)
                for ind, task in enumerate(tasks, start=1):
                    task.team_name = self.teams_repository.get_team_by_id(task.team_id).name

        return tasks

    def get_task_by_id(self, task_id):
        document = self.collection.find_one({"_id": ObjectId(task_id)})
        if not document:
            raise NotFound("Task not found")
        return Task(**document)

    def get_tasks_by_team_id(self, team_id):
        documents = self.collection.find({"team_id": team_id})
        tasks = []
        for doc in documents:
            tasks.append(Task(**doc))
        return tasks

    def get_tasks_by_challenge_id(self, challenge_id):
        documents = self.collection.find({"challenge_id": challenge_id})
        tasks = []
        for doc in documents:
            tasks.append(Task(**doc))
        return tasks

    def get_task_by_team_and_challenge(self, team_id, challenge_name: str = "DO2025"):
        challenge = self.challenge_repository.get_challenge_by_name(challenge_name)
        document = self.collection.find_one({"team_id": team_id, "challenge_id": challenge.id})
        if not document:
            raise NotFound("Task not found")
        return Task(**document)

    def update_task(self, task_id, update_data):
        update_data['updated_at'] = datetime.utcnow()
        result = self.collection.update_one({"_id": ObjectId(task_id)}, {"$set": update_data})
        if result.matched_count == 0:
            raise NotFound("Task not found")
        return result.modified_count

    def delete_task(self, task_id):
        result = self.collection.delete_one({"_id": ObjectId(task_id)})
        if result.deleted_count == 0:
            raise NotFound("Task not found")
        return result.deleted_count

    def get_available_tokens_by_team(self, team_id: str, challenge_name: str = None):
        if challenge_name:
            challenge_repository = ChallengeRepository(self.db)
            challenge = challenge_repository.get_challenge_by_name(challenge_name)
            query = {"team_id": team_id, "challenge_id": challenge.id}
        else:
            query = {"team_id": team_id}
        documents = self.collection.find(query, {'available_tokens': 1, 'challenge_id': 1, 'benchmarks': 1, 'available_benchmarks': 1})

        return list(documents)[0]

    def freeze_scores(self):
        documents = self.collection.find()
        for doc in documents:
            task = Task(**doc)
            update_data = {
                "frozen_benchmark_score": task.best_benchmark_score,
                "status": "frozen"
            }
            self.update_task(str(task.id), update_data)
        return True

    def complete_all(self):
        documents = self.collection.find()
        for doc in documents:
            task = Task(**doc)
            update_data = {
                "status": "completed"
            }
            self.update_task(str(task.id), update_data)
        return True