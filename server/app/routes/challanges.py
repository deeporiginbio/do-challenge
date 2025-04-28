from datetime import datetime

from flasgger import swag_from
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest

from app.config.core import settings
from app.models.db import get_database
from app.repositories.challanges_repository import ChallengeRepository
from app.routes.utils import admin_required

db = get_database()

challenges_blueprint = Blueprint('challenges', __name__)


@challenges_blueprint.route('/', methods=['POST'])
@swag_from({
    'tags': ['Challenges'],
    'summary': 'Create a new Challange',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string', 'description': 'The title of the challenge'},
                    'description': {'type': 'string', 'description': 'The description of the challenge'},
                    'initial_tokens': {'type': 'integer', 'description': 'The number of tokens for the challenge'},
                    'benchmarks': {'type': 'integer', 'description': 'The number of benchmarks for the challenge'}
                },
                'required': ['title', 'description']
            }
        }

    ],
    'responses': {
        '201': {
            'description': 'Task created successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                }
            }
        },
        '400': {
            'description': 'Invalid request'
        }
    }
})
@admin_required
def create_challenge():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    initial_tokens = data.get('tokens', settings.CHALLENGE_INITIAL_TOKENS)
    free_benchmarks = data.get('benchmarks', settings.CHALLENGE_BENCHMARKS)
    if not title or not description:
        raise BadRequest("Missing required fields to create a challenge (title, description, difficulty)")

    challenge_repository = ChallengeRepository(db)
    challenge_id = challenge_repository.create_challenge(title=title, description=description, initial_tokens=initial_tokens,
                                          free_benchmarks=free_benchmarks)
    return jsonify({"message": "Challenge created successfully", "challenge_id": challenge_id}), 201


@challenges_blueprint.route('/', methods=['GET'])
@swag_from({
    'tags': ['Challenges'],
    'summary': 'Get all tasks',
    'parameters': [
        {
            'name': 'title',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Filter challenges by title'
        },
    ],
    'responses': {
        '200': {
            'description': 'List of challenges',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        "created_at": {"type": "string"},
                        "description": {"type": "string"},
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "initial_tokens": {"type": "integer"},
                        "updated_at": {"type": "string"}
                    }
                }
            }
        },
        '400': {
            'description': 'Invalid request'
        }
    }
})
@admin_required
def get_all_challenges():
    title = request.args.get('title')
    challenge_repository = ChallengeRepository(db)

    if title:
        challenge = challenge_repository.get_challenge_by_name(title)
        return challenge.model_dump(exclude_none=True)

    challenges = challenge_repository.get_all_challenges()
    return [challenge.model_dump(exclude_none=True) for challenge in challenges]


@challenges_blueprint.route('/<challenge_id>', methods=['GET'])
@swag_from({
    'tags': ['Challenges'],
    'summary': 'Get challenge by ID',
    'parameters': [
        {
            'name': 'challenge_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'The ID of the challenge to retrieve'
        }
    ],
    'responses': {
        '200': {
            'description': 'Challenge details',
            'schema': {
                'type': 'object',
                'properties': {
                    "created_at": {"type": "string"},
                    "description": {"type": "string"},
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "initial_tokens": {"type": "integer"},
                    "updated_at": {"type": "string"}
                }
            }
        },
        '404': {
            'description': 'Task not found'
        }
    }
})
@admin_required
def get_challenge(challenge_id):
    challenge_repository = ChallengeRepository(db)
    challenge = challenge_repository.get_challenge_by_id(challenge_id)

    return challenge.model_dump(exclude_none=True)


@challenges_blueprint.route('/<challenge_id>', methods=['PUT'])
@swag_from({
    'tags': ['Challenges'],
    'summary': 'Update a challenge',
    'parameters': [
        {
            'name': 'challenge_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'The ID of the challenge to retrieve'
        }
    ],
    'responses': {
        '200': {
            'description': 'Challenge updated successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'}
                }
            }
        },
        '400': {
            'description': 'Invalid request'
        }
    }
})
@admin_required
def update_challenge(challenge_id):
    data = request.get_json()
    update_data = {key: value for key, value in data.items() if key in ["title", "description", "difficulty"]}

    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400

    update_data["updated_at"] = datetime.utcnow()

    challenge_repository = ChallengeRepository(db)
    challenge_repository.update_challenge(challenge_id, update_data)

    return jsonify({"message": "Challenge updated successfully"})


@challenges_blueprint.route('/<challenge_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Challenges'],
    'summary': 'Delete a challenge',
    'parameters': [
        {
            'name': 'challenge_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'The ID of the challenge to retrieve'
        }
    ],
    'responses': {
        '200': {
            'description': 'Challenge deleted successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'}
                }
            }
        },
        '404': {
            'description': 'Challenge not found'
        }
    }
})
@admin_required
def delete_challenge(challenge_id):
    challenge_repository = ChallengeRepository(db)
    challenge_repository.delete_challenge(challenge_id)

    return jsonify({"message": "Challenge deleted successfully"})
