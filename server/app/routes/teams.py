from flasgger import swag_from
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest

from app.models.db import get_database
from app.repositories.teams_repository import TeamsRepository
from app.routes.utils import admin_required

db = get_database()

teams_blueprint = Blueprint('teams', __name__)

@teams_blueprint.route('/', methods=['POST'])
@swag_from({
    'tags': ['Teams'],
    'summary': 'Create a new team',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'team_name': {'type': 'string'}
                },
                'required': ['team_name']
            }
        }
    ],
    'responses': {
        '201': {
            'description': 'Team created successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'team_id': {'type': 'string'},
                    'secret_key': {'type': 'string'}
                }
            }
        },
        '400': {'description': 'Invalid input'}
    }
})
@admin_required
def create_team():
    data = request.get_json()
    team_name = data.get('name')
    if not team_name:
        raise BadRequest("team_name is required")

    teams_repository = TeamsRepository(db)
    if teams_repository.get_team_by_name(team_name):
        raise BadRequest("Team name already exists")

    result = teams_repository.create_team(team_name=team_name)
    return jsonify({"message": "Team created successfully", "team_id": result[0], "password": result[1]})


@teams_blueprint.route('/', methods=['GET'])
@swag_from({
    'tags': ['Teams'],
    'summary': 'Retrieve all teams with optional filtering',
    'parameters': [
        {
            'name': 'team_name',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Filter teams by name'
        }
    ],
    'responses': {
        '200': {
            'description': 'A list of teams',
            'schema': {
                'type': 'object',
                'properties': {
                    'teams': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'team_id': {'type': 'string'},
                                'name': {'type': 'string'},
                                'hashed_secret_key': {'type': 'string'},
                            }
                        }
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
def get_all_teams():
    name_filter = request.args.get('name')
    teams_repository = TeamsRepository(db)
    if name_filter:
        teams = teams_repository.get_all_teams(filter_by_name=name_filter)
    else:
        teams = teams_repository.get_all_teams()
    return [team.model_dump(exclude_none=True) for team in teams]


@teams_blueprint.route('/<team_id>', methods=['GET'])
@swag_from({
    'tags': ['Teams'],
    'summary': 'Retrieve team information by ID',
    'parameters': [
        {
            'name': 'team_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'The ID of the team to retrieve'
        }
    ],
    'responses': {
        '200': {
            'description': 'Team information',
            'schema': {
                'type': 'object',
                'properties': {
                    'team_id': {'type': 'string'},
                    'name': {'type': 'string'},
                    'hashed_secret_key': {'type': 'string'}
                }
            }
        },
        '404': {
            'description': 'Team not found'
        }
    }
})
@admin_required
def get_team_info(team_id):
    teams_repository = TeamsRepository(db)
    team = teams_repository.get_team_by_id(team_id)
    return team.model_dump(exclude_none=True)


@teams_blueprint.route('/<team_id>', methods=['PUT'])
@swag_from({
    'tags': ['Teams'],
    'summary': 'Update team information by ID',
    'parameters': [
        {
            'name': 'team_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'The ID of the team to update'
        }
    ],
    'requestBody': {
        'required': True,
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'}
                    }
                }
            }
        }
    },
    'responses': {
        '200': {
            'description': 'Team updated successfully',
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
def update_team(team_id):
    data = request.get_json()
    update_data = {key: value for key, value in data.items() if
                   key in ["name"]}

    teams_repository = TeamsRepository(db)
    teams_repository.update_team(team_id, update_data)

    return jsonify({"message": "Team updated successfully"})


@teams_blueprint.route('/<team_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Teams'],
    'summary': 'Delete a team by ID',
    'parameters': [
        {
            'name': 'team_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'The ID of the team to delete'
        }
    ],
    'responses': {
        '200': {
            'description': 'Team deleted successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'}
                }
            }
        },
        '404': {
            'description': 'Team not found'
        }
    }
})
@admin_required
def delete_team(team_id):
    teams_repository = TeamsRepository(db)
    teams_repository.delete_team(team_id)

    return jsonify({"message": "Team deleted successfully"})
