from flasgger import swag_from
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest, Forbidden

from app.models.db import get_database
from app.repositories.task_repository import TaskRepository
from app.repositories.teams_repository import TeamsRepository
from app.routes.utils import admin_required, login_required

db = get_database()

tasks_blueprint = Blueprint('tasks', __name__)


@tasks_blueprint.route('/', methods=['POST'])
@swag_from({
    'tags': ['Tasks'],
    'summary': 'Create a new task',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'team_id': {'type': 'string', 'description': 'The ID of the team'},
                    'challenge_id': {'type': 'string', 'description': 'The ID of the challenge'},
                    'id_mappings': {'type': 'object', 'description': 'The id mappings'},
                },
                'required': ['team_id', 'challenge_id']
            }
        }

    ],
    'responses': {
        '200': {
            'description': 'Task created successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'task_id': {'type': 'string'}
                }
            }
        },
        '400': {
            'description': 'Invalid request'
        }
    }
})
@admin_required
def create_task():
    data = request.get_json()
    team_id = data.get('team_id')
    challenge_id = data.get('challenge_id')

    if not team_id or not challenge_id:
        raise BadRequest("Missing required fields (team_id or challenge_id)")

    task_repository = TaskRepository(db)
    id_mappings = data.get('id_mappings', None)
    result = task_repository.create_task(team_id=team_id, challenge_id=challenge_id, id_mappings=id_mappings)
    return jsonify({"message": "Task created successfully", "task_id": result})

@tasks_blueprint.route('/freeze', methods=['POST'])
@swag_from({
    'tags': ['Tasks'],
    'summary': 'Freeze all tasks scores',
    'parameters': [
    ],
    'responses': {
        '200': {
            'description': 'Tasks scores frozen successfully',
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
@login_required
def freeze_scores(secret_key: str):
    team = TeamsRepository(db).get_team_by_secret_key(secret_key)
    if team.name != "Admin":
        raise Forbidden("Only Admin can freeze scores")
    task_repository = TaskRepository(db)
    task_repository.freeze_scores()
    return jsonify({"message": "Scores frozen successfully"})

@tasks_blueprint.route('', methods=['GET'])
@swag_from({
    'tags': ['Tasks'],
    'summary': 'Get all tasks',
    'parameters': [
        {
            'name': 'challenge_id',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Filter tasks by challenge ID'
        },
        {
            'name': 'ranked',
            'in': 'query',
            'type': 'boolean',
            'required': False,
            'description': 'Whether to rank tasks by their best benchmark score'
        }
    ],
    'responses': {
        '200': {
            'description': 'List of tasks',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'available_tokens': {'type': 'integer'},
                        'best_benchmark_score': {'type': 'number'},
                        'challenge_id': {'type': 'string'},
                        'created_at': {'type': 'string'},
                        'id': {'type': 'string'},
                        'requested_correct_ids': {'type': 'array', 'items': {'type': 'integer'}},
                        'status': {'type': 'string'},
                        'team_id': {'type': 'string'},
                        'tokens': {'type': 'integer'},
                        'updated_at': {'type': 'string'}
                    }
                }
            }
        },
        '400': {
            'description': 'Invalid request'
        }
    }
})
@login_required
def get_all_tasks(secret_key: str):
    challenge_id = request.args.get('challenge_id')
    ranked = request.args.get('ranked')

    task_repository = TaskRepository(db)
    tasks = task_repository.get_all(team_secret_key=secret_key, challenge_id=challenge_id, ranked=ranked)

    return [task.model_dump() for task in tasks]


@tasks_blueprint.route('/<task_id>', methods=['GET'])
@swag_from({
    'tags': ['Tasks'],
    'summary': 'Get task by ID',
    'parameters': [
        {
            'name': 'task_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'The ID of the task to retrieve'
        }
    ],
    'responses': {
        '200': {
            'description': 'Task details',
            'schema': {
                'type': 'object',
                'properties': {
                    'available_tokens': {'type': 'integer'},
                    'best_benchmark_score': {'type': 'number'},
                    'challenge_id': {'type': 'string'},
                    'created_at': {'type': 'string'},
                    'id': {'type': 'string'},
                    'last_benchmark_score': {'type': 'number'},
                    'requested_correct_ids': {'type': 'array', 'items': {'type': 'integer'}},
                    'status': {'type': 'string'},
                    'team_id': {'type': 'string'},
                    'tokens': {'type': 'integer'},
                    'updated_at': {'type': 'string'}
                }
            }
        },
        '404': {
            'description': 'Task not found'
        }
    }
})
@admin_required
def get_task(task_id: str):
    task_repository = TaskRepository(db)
    task = task_repository.get_task_by_id(task_id)

    return task.model_dump(exclude_none=True)


@tasks_blueprint.route('/<task_id>', methods=['PUT'])
@swag_from({
    'tags': ['Tasks'],
    'summary': 'Update a task',
    'parameters': [
        {
            'name': 'task_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'The ID of the task to update'
        }
    ],
    'requestBody': {
        'required': True,
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'description': 'The new status of the task'},
                        'tokens': {'type': 'integer', 'description': 'The number of tokens to update'}
                    }
                }
            }
        }
    },
    'responses': {
        '200': {
            'description': 'Task updated successfully',
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
def update_task(task_id: str):
    data = request.get_json()
    updates = {k: v for k, v in data.items() if k in ['status', 'available_tokens', 'available_benchmarks']}

    task_repository = TaskRepository(db)
    task_repository.update_task(task_id, updates)

    return jsonify({"message": "Task updated successfully"})


@tasks_blueprint.route('/<task_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Tasks'],
    'summary': 'Delete a task',
    'parameters': [
        {
            'name': 'task_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'The ID of the task to delete'
        }
    ],
    'responses': {
        '200': {
            'description': 'Task deleted successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'}
                }
            }
        },
        '404': {
            'description': 'Task not found'
        }
    }
})
@admin_required
def delete_task(task_id: str):
    task_repository = TaskRepository(db)
    task_repository.delete_task(task_id)

    return jsonify({"message": "Task deleted successfully"})
