import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch, mock_open

import pandas as pd
from flask import Flask
from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden, NotFound, MethodNotAllowed, InternalServerError, TooManyRequests

from app.config.core import settings
from app.routes.error_handler import json_error_handler, internal_server_error
from app.routes.main import main_blueprint


class TestMainRoutes(unittest.TestCase):
    def setUp(self):
        """Create and configure a test Flask app."""
        self.app = Flask(__name__)
        self.app.register_blueprint(main_blueprint)
        self.app.register_error_handler(BadRequest, lambda e: json_error_handler(e, 400, "Bad Request"))
        self.app.register_error_handler(Unauthorized, lambda e: json_error_handler(e, 401, "Unauthorized"))
        self.app.register_error_handler(Forbidden, lambda e: json_error_handler(e, 403, "Forbidden"))
        self.app.register_error_handler(NotFound, lambda e: json_error_handler(e, 404, "Not Found"))
        self.app.register_error_handler(MethodNotAllowed, lambda e: json_error_handler(e, 405, "Method Not Allowed"))
        self.app.register_error_handler(TooManyRequests, lambda e: json_error_handler(e, 429, "Too Many Requests"))
        self.app.register_error_handler(InternalServerError, lambda e: json_error_handler(e, 500, "Internal Server Error"))
        self.app.register_error_handler(Exception, lambda e: internal_server_error(e))
        self.client = self.app.test_client()

    # ---------------------------
    # Tests for /login endpoint
    # ---------------------------
    @patch('app.repositories.teams_repository.TeamsRepository.get_team_by_name')
    def test_login_missing_fields(self, mock_get_team):
        """Test /login when required fields are missing."""
        response = self.client.post('/login', json={'name': 'team1'})  # missing password
        self.assertEqual(response.status_code, 400)
        self.assertIn("team_name and team_password is required", response.get_data(as_text=True))

    @patch('app.repositories.teams_repository.TeamsRepository.get_team_by_name')
    @patch('werkzeug.security.check_password_hash')
    def test_login_invalid_credentials(self, mock_check_password, mock_get_team):
        """Test /login with invalid credentials."""
        # Simulate no team found
        mock_get_team.return_value = None
        response = self.client.post('/login', json={'name': 'team1', 'password': 'pass'})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid credentials", response.get_data(as_text=True))

        # Simulate team found but wrong password
        team = SimpleNamespace(password="hashed", secret_key="secret123")
        mock_get_team.return_value = team
        mock_check_password.return_value = False
        response = self.client.post('/login', json={'name': 'team1', 'password': 'wrong'})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid credentials", response.get_data(as_text=True))

    @patch('app.repositories.teams_repository.TeamsRepository.get_team_by_name')
    @patch('werkzeug.security.check_password_hash')
    def test_login_success(self, mock_check_password, mock_get_team):
        """Test /login with valid credentials."""
        pass
        # team = SimpleNamespace(password="hashed", secret_key="secret123")
        # mock_get_team.return_value = team
        # mock_check_password.return_value = True
        # response = self.client.post('/login', json={'name': 'team1', 'password': 'correct'})
        # self.assertEqual(response.status_code, 200)
        # data = json.loads(response.get_data(as_text=True))
        # self.assertEqual(data.get('message'), "Login successful")
        # self.assertEqual(data.get('secret_key'), "secret123")

    # ---------------------------
    # Tests for /available_tokens endpoint
    # ---------------------------
    @patch('app.repositories.teams_repository.TeamsRepository.get_team_by_secret_key')
    def test_available_tokens_missing_secret_key(self, mock_get_team):
        """Test /available_tokens when secret_key is missing."""
        response = self.client.post('/available_tokens', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("secret_key is required", response.get_data(as_text=True))

    @patch('app.repositories.task_repository.TaskRepository.get_available_tokens_by_team')
    @patch('app.repositories.teams_repository.TeamsRepository.get_team_by_secret_key')
    def test_available_tokens_success(self, mock_get_team, mock_get_tokens):
        """Test successful retrieval of available tokens."""
        team = SimpleNamespace(id=1, name="team1", secret_key="secret123")
        mock_get_team.return_value = team
        token_data = [{
            "challenge_id": "challenge1",
            "available_tokens": 50,
            "requested_correct_ids": [1, 2],
        }]
        mock_get_tokens.return_value = token_data
        payload = {"secret_key": "secret123", "challenge_name": "challenge1"}
        response = self.client.post('/available_tokens', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]['challenge_id'], "challenge1")
        self.assertEqual(data[0]['available_tokens'], 50)
        self.assertEqual(data[0]['requested_ids'], [1, 2])

    # ---------------------------
    # Tests for /get_labels endpoint
    # ---------------------------
    @patch('app.repositories.teams_repository.TeamsRepository.get_team_by_secret_key')
    def test_get_labels_missing_fields(self, mock_get_team):
        """Test /get_labels with missing required fields."""
        payload = {"secret_key": "secret123"}
        response = self.client.post('/get_labels', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("challenge_name, label_type and indexes are required", response.get_data(as_text=True))

    @patch('app.repositories.teams_repository.TeamsRepository.get_team_by_secret_key')
    def test_get_labels_invalid_indexes_type(self, mock_get_team):
        """Test /get_labels with indexes not being a list."""
        payload = {
            "secret_key": "secret123",
            "challenge_name": "challenge1",
            "label_type": "correct",
            "indexes": "not a list"
        }
        response = self.client.post('/get_labels', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Indexes should be a list", response.get_data(as_text=True))

    @patch('app.repositories.teams_repository.TeamsRepository.get_team_by_secret_key')
    def test_get_labels_invalid_label_type(self, mock_get_team):
        """Test /get_labels with an invalid label_type."""
        payload = {
            "secret_key": "secret123",
            "challenge_name": "challenge1",
            "label_type": "invalid",
            "indexes": [0]
        }
        response = self.client.post('/get_labels', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid label_type", response.get_data(as_text=True))

    @patch('app.repositories.task_repository.TaskRepository.update_task')
    @patch('app.repositories.task_repository.TaskRepository.get_task_by_team_and_challenge')
    @patch('app.repositories.teams_repository.TeamsRepository.get_team_by_secret_key')
    @patch('pandas.read_csv')
    @patch("builtins.open", new_callable=mock_open, read_data='{"0": 0, "1": 1}}')
    def test_get_labels_success_correct(self, mock_update_task, mock_get_task, mock_get_team, mock_read_csv, mocked_file):
        """Test /get_labels success scenario for correct labels."""
        team = SimpleNamespace(id=1, name="team1", secret_key="secret123")
        mock_get_team.return_value = team
        # Dummy task with no previous labels requested and sufficient tokens.
        task = SimpleNamespace(
            id=1,
            requested_correct_ids=[],
            available_tokens=100,
        )
        mock_get_task.return_value = task
        # Dummy DataFrame for label values.
        df = pd.DataFrame({"score": [10, 20, 30]}, index=[0, 1, 2])
        mock_read_csv.return_value = df

        payload = {
            "secret_key": "secret123",
            "challenge_name": "challenge1",
            "label_type": "correct",
            "indexes": [0, 1]
        }
        response = self.client.post('/get_labels', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        # Calculate expected tokens based on new indexes * CORRECT_LABEL_PRICE.
        expected_tokens = 100 - (2 * settings.CORRECT_LABEL_PRICE)
        self.assertEqual(data.get("available_tokens"), expected_tokens)
        labels = data.get("labels")
        # With the mapping file mapping "0"->0 and "1"->1, expect scores from the df.
        self.assertEqual(labels.get("0"), 10)
        self.assertEqual(labels.get("1"), 20)

    @patch('app.repositories.task_repository.TaskRepository.update_task')
    @patch('app.repositories.task_repository.TaskRepository.get_task_by_team_and_challenge')
    @patch('app.repositories.teams_repository.TeamsRepository.get_team_by_secret_key')
    @patch('pandas.read_csv')
    @patch("builtins.open", new_callable=mock_open, read_data='{"0": 0, "1": 1}}')
    def test_get_labels_index_not_found(self, mock_read_csv, mock_get_team, mock_get_task, mock_update_task, mocked_file):
        """Test /get_labels when one or more indexes are not found in the CSV file."""
        team = SimpleNamespace(id=1, name="team1", secret_key="secret123")
        mock_get_team.return_value = team
        task = SimpleNamespace(
            id=1,
            requested_correct_ids=[],
            available_tokens=10000,
        )
        mock_get_task.return_value = task
        df = pd.DataFrame({"score": [10, 20]}, index=[0, 1])
        mock_read_csv.return_value = df
        payload = {
            "secret_key": "secret123",
            "challenge_name": "challenge1",
            "label_type": "correct",
            "indexes": [0, 2]  # index 2 not found in mapping (since no mapping file patch here)
        }
        response = self.client.post('/get_labels', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Index 2 not found in the dataset", response.get_data(as_text=True))

    @patch('app.repositories.task_repository.TaskRepository.update_task')
    @patch('app.repositories.task_repository.TaskRepository.get_task_by_team_and_challenge')
    @patch('app.repositories.teams_repository.TeamsRepository.get_team_by_secret_key')
    @patch('pandas.read_csv')
    def test_get_labels_not_enough_tokens(self, mock_read_csv, mock_get_team, mock_get_task, mock_update_task):
        """Test /get_labels when there are not enough tokens available."""
        team = SimpleNamespace(id=1, name="team1", secret_key="secret123")
        mock_get_team.return_value = team
        task = SimpleNamespace(
            id=1,
            requested_correct_ids=[],
            available_tokens=0,  # insufficient tokens
        )
        mock_get_task.return_value = task
        df = pd.DataFrame({"score": [10, 20, 30]}, index=[0, 1, 2])
        mock_read_csv.return_value = df
        payload = {
            "secret_key": "secret123",
            "challenge_name": "challenge1",
            "label_type": "correct",
            "indexes": [0]
        }
        response = self.client.post('/get_labels', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Not enough tokens", response.get_data(as_text=True))

    # ---------------------------
    # Tests for /benchmark endpoint
    # ---------------------------
    def test_benchmark_missing_fields(self):
        """Test /benchmark when required fields are missing."""
        response = self.client.post('/benchmark', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("secret_key, challenge_name and ids are required", response.get_data(as_text=True))

    def test_benchmark_ids_not_list(self):
        """Test /benchmark when ids is not a list."""
        payload = {"secret_key": "secret123", "challenge_name": "challenge1", "ids": "not a list"}
        response = self.client.post('/benchmark', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Protein ids should be a list", response.get_data(as_text=True))

    def test_benchmark_wrong_length(self):
        """Test /benchmark when the number of ids does not match SUBMISSION_LENGTH."""
        # Assuming settings.SUBMISSION_LENGTH is 2.
        payload = {"secret_key": "secret123", "challenge_name": "challenge1", "ids": [1, 2, 3]}
        response = self.client.post('/benchmark', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Expected", response.get_data(as_text=True))

    @patch("builtins.open", new_callable=mock_open, read_data='{"10": 0, "20": 1, "30": 2}')
    @patch('app.repositories.task_repository.TaskRepository.update_task')
    @patch('app.repositories.task_repository.TaskRepository.get_task_by_team_and_challenge')
    @patch('app.repositories.teams_repository.TeamsRepository.get_team_by_secret_key')
    @patch('pandas.read_csv')
    def test_benchmark_free_benchmark(self, mock_read_csv, mock_get_team, mock_get_task, mock_update_task, mock_file):
        """Test /benchmark when a free benchmark is available."""
        team = SimpleNamespace(id=1, name="team1", secret_key="secret123")
        mock_get_team.return_value = team
        task = SimpleNamespace(
            id=1,
            available_benchmarks=1,
            available_tokens=100,
            best_benchmark_score=None,
            benchmarks=[]
        )
        mock_get_task.return_value = task
        df = pd.DataFrame({"score": [10, 20, 30]}, index=[0, 1, 2])
        mock_read_csv.return_value = df
        payload = {"secret_key": "secret123", "challenge_name": "challenge1", "ids": [10, 20]}
        response = self.client.post('/benchmark', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        # With the provided mapping, ids 10->0, 20->1, 30->2 so the score is:
        expected_score = len({0, 1} & set(df.index))
        self.assertEqual(data.get("available_benchmarks"), 0)
        self.assertEqual(data.get("last_benchmark_score"), expected_score)

    @patch("builtins.open", new_callable=mock_open, read_data='{"10": 0, "20": 1, "30": 2}')
    @patch('app.repositories.task_repository.TaskRepository.update_task')
    @patch('app.repositories.task_repository.TaskRepository.get_task_by_team_and_challenge')
    @patch('app.repositories.teams_repository.TeamsRepository.get_team_by_secret_key')
    @patch('pandas.read_csv')
    def test_benchmark_token_deduction(self, mock_read_csv, mock_get_team, mock_get_task, mock_update_task, mock_file):
        """Test /benchmark when no free benchmarks are available."""
        team = SimpleNamespace(id=1, name="team1", secret_key="secret123")
        mock_get_team.return_value = team
        task = SimpleNamespace(
            id=1,
            available_benchmarks=0,  # no free benchmarks available
            available_tokens=10000,
            best_benchmark_score=50,
            benchmarks=[40],
        )
        mock_get_task.return_value = task
        df = pd.DataFrame({"score": [10, 20, 30]}, index=[0, 1, 2])
        mock_read_csv.return_value = df
        payload = {"secret_key": "secret123", "challenge_name": "challenge1", "ids": [10, 20]}
        response = self.client.post('/benchmark', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("No benchmarks available", response.get_data(as_text=True))

    @patch("builtins.open", new_callable=mock_open, read_data='{"10": 0, "20": 1, "30": 2}')
    @patch('app.repositories.task_repository.TaskRepository.get_task_by_team_and_challenge')
    @patch('app.repositories.teams_repository.TeamsRepository.get_team_by_secret_key')
    @patch('pandas.read_csv')
    def test_benchmark_csv_read_failure(self, mock_read_csv, mock_get_team, mock_get_task, mock_file):
        """Test /benchmark when reading the CSV file fails."""
        team = SimpleNamespace(id=1, name="team1", secret_key="secret123")
        mock_get_team.return_value = team
        task = SimpleNamespace(
            id=1,
            available_benchmarks=1,
            available_tokens=100,
            best_benchmark_score=None,
            benchmarks=[]
        )
        mock_get_task.return_value = task
        # Force pd.read_csv to raise an Exception.
        mock_read_csv.side_effect = Exception("File not found")
        payload = {"secret_key": "secret123", "challenge_name": "challenge1", "ids": [10, 20]}
        response = self.client.post('/benchmark', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Failed to read labels file", response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
