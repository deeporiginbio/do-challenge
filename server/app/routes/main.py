import json
import os
import pickle
from datetime import datetime

import pandas as pd
from flasgger import swag_from
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden
from werkzeug.security import check_password_hash

from app.config.core import settings
from app.models.db import get_database
from app.repositories.challanges_repository import ChallengeRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.teams_repository import TeamsRepository
from app.routes.utils import login_required, generate_hash

db = get_database()
main_blueprint = Blueprint('main', __name__)


@main_blueprint.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Main'],
    'summary': 'Login to the platform',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'description': 'Team name'},
                    'password': {'type': 'string', 'description': 'Team password'},
                },
                'required': ['name', 'password']
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Successful login',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'secret_key': {'type': 'string'}
                }
            }
        },
        '400': {'description': 'Invalid request'},
        '401': {'description': 'Invalid credentials'}
    }
})
def login():
    """
    Authenticates team credentials and returns a secret key.
    """
    data = request.get_json()
    if not data:
        raise BadRequest("Invalid JSON payload")
    name = data.get('name')
    password = data.get('password')
    if not name or not password:
        raise BadRequest("Team name and password are required")
    team = TeamsRepository(db).get_team_by_name(name)

    if not team or not check_password_hash(team.password, password):
        raise Unauthorized("Invalid credentials")

    return jsonify({"message": "Login successful", "secret_key": team.secret_key, "is_admin": team.name == "Admin"}), 200

@main_blueprint.route('/remained_budget', methods=['GET'])
@swag_from({
    'tags': ['Main'],
    'summary': 'Get available tokens for a team by challenge',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'challenge_name': {'type': 'string', 'description': 'The challenge name'},
                },
                'required': ['secret_key', 'challenge_name']
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'List of tokens for the team',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'challenge_id': {'type': 'string'},
                        'available_tokens': {'type': 'integer'},
                        'requested_ids': {
                            'type': 'array',
                            'items': {'type': 'integer'}
                        }
                    }
                }
            }
        },
        '400': {'description': 'Invalid request'},
        '401': {'description': 'Unauthorized'}
    }
})
@login_required
def get_available_tokens(secret_key: str):
    team = TeamsRepository(db).get_team_by_secret_key(secret_key)
    if not team:
        raise Unauthorized("Invalid team secret key")
    task_repository = TaskRepository(db)
    available_tokens = task_repository.get_available_tokens_by_team(team.id, settings.CHALLENGE_NAME)
    response_data = {
        "available_tokens": available_tokens["available_tokens"],
        "benchmarks": available_tokens.get("benchmarks", []),
        "available_benchmarks": available_tokens.get("available_benchmarks", 0),
    }
    return jsonify(response_data), 200

@main_blueprint.route('/requested_ids', methods=['GET'])
@login_required
def get_requested_ids(secret_key: str):
    team = TeamsRepository(db).get_team_by_secret_key(secret_key)
    if not team:
        raise Unauthorized("Invalid team secret key")

    task_repository = TaskRepository(db)
    task = task_repository.get_task_by_team_and_challenge(team.id, settings.CHALLENGE_NAME)
    return jsonify({"requested_ids": task.requested_correct_ids}), 200

@main_blueprint.route('/lab_experiment', methods=['POST'])
@swag_from({
    'tags': ['Main'],
    'summary': 'Retrieve labels for a given team',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'challenge_name': {'type': 'string', 'description': 'Challenge name'},
                    'label_type': {'type': 'string', 'description': 'Label type'},
                    'indexes': {
                        'type': 'array',
                        'items': {'type': 'integer'},
                        'description': 'List of indexes'
                    }
                },
                'required': ['challenge_name', 'label_type', 'indexes']
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Labels retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'labels': {
                        'type': 'object',
                        'additionalProperties': {'type': 'number'}
                    },
                    'available_tokens': {'type': 'number'}
                }
            }
        },
        '400': {'description': 'Invalid request'},
        '401': {'description': 'Unauthorized'}
    }
})
@login_required
def get_labels(secret_key: str):
    """
    Retrieves labels for the provided indexes for an authenticated team.
    """
    data = request.get_json()
    if not data:
        raise BadRequest("Invalid JSON payload")
    indexes = data.get('ids')
    if indexes is None:
        raise BadRequest("ids are required")

    if not isinstance(indexes, list):
        raise BadRequest("Indexes should be a list")

    validated_ids = []
    for idx in indexes:
        if not (isinstance(idx, int) or (isinstance(idx, str) and idx.isdigit())):
            raise BadRequest("Indexes should be a list of integers or numeric strings")
        validated_ids.append(int(idx))

    team = TeamsRepository(db).get_team_by_secret_key(secret_key)
    if not team:
        raise Unauthorized("Invalid team secret key")
    task_repository = TaskRepository(db)
    task = task_repository.get_task_by_team_and_challenge(team.id, settings.CHALLENGE_NAME)

    if task.status == "completed":
        raise BadRequest("Challenge already completed")

    requested_set = set(validated_ids)
    correct_set = set(task.requested_correct_ids)
    task.requested_correct_ids += list(requested_set - correct_set)
    token_cost = len(requested_set - correct_set) * settings.CORRECT_LABEL_PRICE

    if task.available_tokens < token_cost:
        raise BadRequest("Not enough tokens")

    task.available_tokens -= token_cost
    
    base_path = settings.DATASETS_PATH
    labels_file = os.path.join(base_path, settings.CHALLENGE_NAME, "labels_df.pkl")
    mappings_file = os.path.join(base_path, settings.CHALLENGE_NAME, f"{team.name}_mappings.pkl")
    try:
        with open(labels_file, "rb") as file:
            df = pickle.load(file)
    except Exception as e:
        raise BadRequest(f"Failed to read labels file: {str(e)}")
    try:
        with open(mappings_file, "rb") as f:
            id_mappings = pickle.load(f)
    except Exception as e:
        raise BadRequest(f"Failed to read mappings file: {str(e)}")

    labels = {}
    for idx in validated_ids:
        if idx in id_mappings:
            correct_label_id = id_mappings[idx]
            try:
                labels[idx] = df.loc[correct_label_id, "score"]
            except KeyError:
                raise BadRequest(f"Label for index {idx} not found in dataset")
        else:
            raise BadRequest(f"Index {idx} not found in the dataset")
    update_data = {
        "available_tokens": task.available_tokens,
        "requested_correct_ids": task.requested_correct_ids,
    }
    task_repository.update_task(task.id, update_data)

    return jsonify({"labels": labels, "available_tokens": task.available_tokens}), 200

@main_blueprint.route('/submit', methods=['POST'])
@swag_from({
    'tags': ['Main'],
    'summary': 'Benchmark model predictions against ground truth',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'challenge_name': {'type': 'string', 'description': 'Challenge name'},
                    'indexes': {
                        'type': 'array',
                        'items': {'type': 'integer'},
                        'description': 'List of protein indexes'
                    }
                },
                'required': ['challenge_name', 'indexes']
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Benchmark completed',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'available_tokens': {'type': 'integer'},
                    'best_benchmark_score': {'type': 'number'},
                    'last_benchmark_score': {'type': 'number'},
                    'benchmarks': {
                        'type': 'array',
                        'items': {'type': 'number'}
                    },
                    'available_benchmarks': {'type': 'integer'}
                }
            }
        },
        '400': {'description': 'Invalid request'},
        '401': {'description': 'Unauthorized'},
        '500': {'description': 'Server error'}
    }
})
@login_required
def benchmark(secret_key: str):
    """
    Benchmarks model predictions for the authenticated team.
    """
    data = request.get_json()
    if not data:
        raise BadRequest("Invalid JSON payload")

    request_indexes = data.get('ids')
    if request_indexes is None:
        raise BadRequest("ids are required")
    if not isinstance(request_indexes, list):
        raise BadRequest("Indexes should be a list")
    if len(request_indexes) != settings.SUBMISSION_LENGTH:
        raise BadRequest(f"Expected {settings.SUBMISSION_LENGTH} indexes, got {len(request_indexes)}")

    validated_ids = []
    for idx in request_indexes:
        if not (isinstance(idx, int) or (isinstance(idx, str) and idx.isdigit())):
            raise BadRequest("Indexes should be a list of integers or numeric strings")
        validated_ids.append(int(idx))

    team = TeamsRepository(db).get_team_by_secret_key(secret_key)
    if not team:
        raise Unauthorized("Invalid team secret key")
    task_repository = TaskRepository(db)
    task = task_repository.get_task_by_team_and_challenge(team.id, settings.CHALLENGE_NAME)

    if task.status == "completed":
        raise BadRequest("Challenge already completed")

    last_benchmark_hash = generate_hash(validated_ids)
    if task.last_benchmark_hash == last_benchmark_hash:
        return jsonify({
            "message": "Submission already benchmarked",
            "available_tokens": task.available_tokens,
            "best_benchmark_score": task.best_benchmark_score,
            "last_benchmark_score": task.benchmarks[-1],
            "benchmarks": task.benchmarks,
            "available_benchmarks": task.available_benchmarks
        }), 200

    update_data = {"last_benchmark_hash": last_benchmark_hash}
    if task.available_benchmarks > 0:
        task.available_benchmarks -= 1
        update_data["available_benchmarks"] = task.available_benchmarks
    else:
        raise BadRequest("No benchmarks available")
    base_path = settings.DATASETS_PATH
    top1000_file = os.path.join(base_path, settings.CHALLENGE_NAME, "top1000_df.pkl")
    try:
        with open(top1000_file, "rb") as f:
            top1000_df = pickle.load(file)
    except Exception as e:
        raise BadRequest(f"Failed to read top1000 file: {str(e)}")
    mappings_file = os.path.join(base_path, settings.CHALLENGE_NAME, f"{team.name}_mappings.pkl")
    try:
        with open(mappings_file, "rb") as f:
            id_mappings = pickle.load(f)
    except Exception as e:
        raise BadRequest(f"Failed to read mappings file: {str(e)}")

    try:
        correct_ids = {id_mappings[int(idx)] for idx in validated_ids}
    except KeyError:
        raise BadRequest("Invalid id provided, please check.")
    score = (len(correct_ids & set(top1000_df.index)) * 100) / len(top1000_df)
    update_data["benchmarks"] = task.benchmarks + [score]
    task.benchmarks = task.benchmarks + [score]
    if not task.best_benchmark_score or score > task.best_benchmark_score:
        update_data["best_benchmark_score"] = score
        task.best_benchmark_score = score
    task_repository.update_task(task.id, update_data)
    return jsonify({
        "message": "Benchmark completed",
        "available_tokens": task.available_tokens,
        "best_benchmark_score": task.best_benchmark_score,
        "last_benchmark_score": score,
        "benchmarks": task.benchmarks,
        "available_benchmarks": task.available_benchmarks
    }), 200

@main_blueprint.route('/start_challenge', methods=['POST'])
@swag_from({
    'tags': ['Challenge'],
    'summary': 'Start a challenge and record start time',
    'responses': {
        '200': {
            'description': 'Challenge started successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'start_time': {'type': 'string'}
                }
            }
        }
    }
})
@login_required
def start_challenge(secret_key: str):
    team = TeamsRepository(db).get_team_by_secret_key(secret_key)
    if team.name != "Admin":
        raise Forbidden("Admin required")

    start_time = ChallengeRepository(db).start_challenge(settings.CHALLENGE_NAME)


    return jsonify({"message": "Challenge started!", "start_time": int(start_time.timestamp() * 1000)}), 200

@main_blueprint.route('/start_time', methods=['GET'])
@swag_from({
    'tags': ['Challenge'],
    'summary': 'Retrieve the recorded challenge start time',
    'responses': {
        '200': {
            'description': 'Start time retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'start_time': {'type': 'string'}
                }
            }
        },
        '404': {'description': 'Start time not found'}
    }
})
@login_required
def get_start_time(secret_key: str):
    challenge = ChallengeRepository(db).get_challenge_by_name(settings.CHALLENGE_NAME)

    if challenge.start_time:
        return jsonify({"start_time": int(challenge.start_time.timestamp() * 1000)}), 200
    return jsonify({"error": "Start time not found"}), 404


@main_blueprint.route('/end_challenge', methods=['POST'])
@login_required
def end_challenge(secret_key: str):
    team = TeamsRepository(db).get_team_by_secret_key(secret_key)
    if team.name != "Admin":
        raise Forbidden("Admin required")

    finished = TaskRepository(db).complete_all()
    if not finished:
        raise BadRequest("Failed to finish all tasks")

    end_time = ChallengeRepository(db).end_challenge(settings.CHALLENGE_NAME)

    return jsonify({"message": "Challenge ended!", "end_time": int(end_time.timestamp() * 1000)}), 200

@main_blueprint.route('/reset', methods=['POST'])
@login_required
def reset(secret_key: str):
    team = TeamsRepository(db).get_team_by_secret_key(secret_key)
    TaskRepository(db).reset_task(team.id)
    return jsonify({"message": "Task reset successfully"}), 200

@main_blueprint.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200