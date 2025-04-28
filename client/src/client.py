import requests
from .configs import Config

from typing import List, Any, Optional
from pydantic import BaseModel

from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field


class RemainedBudgetResponse(BaseModel):
    """
    Model representing the remaining budget response from the API.
    """
    available_benchmarks: int = Field(
        ...,
        description="The number of benchmarks that are currently available."
    )
    available_tokens: int = Field(
        ...,
        description="The number of tokens that are currently available."
    )
    benchmarks: List[float] = Field(
        ...,
        description="A list of benchmark values represented as floats."
    )


class RequestedIDsResponse(BaseModel):
    """
    Model representing the response that includes requested IDs.
    """
    requested_ids: List[int] = Field(
        ...,
        description="A list of requested IDs provided by the API."
    )


class LabExperimentResponse(BaseModel):
    """
    Model representing the lab experiment response from the API.
    """
    available_tokens: int = Field(
        ...,
        description="The number of tokens available after the lab experiment."
    )
    labels: Dict[str, float] = Field(
        ...,
        description="A dictionary mapping label names to their corresponding float values."
    )


class SubmitResponse(BaseModel):
    """
    Model representing the submission response from the API.
    """
    available_benchmarks: int = Field(
        ...,
        description="The number of benchmarks available after submission."
    )
    available_tokens: int = Field(
        ...,
        description="The number of tokens available after submission."
    )
    benchmarks: List[Any] = Field(
        ...,
        description="A list containing benchmark details; structure may vary."
    )
    best_benchmark_score: float = Field(
        ...,
        description="The best benchmark score achieved from the submission."
    )
    last_benchmark_score: float = Field(
        ...,
        description="The most recent benchmark score recorded from the submission."
    )


class APIErrorResponse(BaseModel):
    """
    Model representing an error response from the API.
    """
    error: str = Field(
        ...,
        description="A short description of the error."
    )
    message: str = Field(
        ...,
        description="A detailed error message providing more context."
    )
    status_code: Optional[int] = Field(
        None,
        description="The HTTP status code returned by the API, if applicable."
    )


class DOChallengeClient:
    """DOChallengeClient class to interact with the challenge server."""

    def __init__(self, secret_key: str):
        self.base_url = Config.BASE_URL
        if not secret_key:
            raise ValueError("secret_key should not be empty")
        self.secret_key = secret_key

    def submit(self, submission_ids: List[int]) -> Any:
        """
        Submits a list of submission IDs to the server.
        Returns:
            SubmitResponse: On success.
            APIErrorResponse: On error.
        """
        if not isinstance(submission_ids, list):
            raise ValueError("ids should be a list")

        if len(submission_ids) != Config.SUBMISSION_LENGTH:
            raise ValueError(f"ids length should be {Config.SUBMISSION_LENGTH}")

        validated_ids = []
        for idx in submission_ids:
            if not (isinstance(idx, int) or (isinstance(idx, str) and idx.isdigit())):
                raise ValueError("Indexes should be a list of integers or numeric strings")
            validated_ids.append(int(idx))

        url = f"{self.base_url}/submit"
        headers = {'x-token': self.secret_key}
        response = requests.post(url, json={'ids': validated_ids}, headers=headers)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            error_json = http_err.response.json()
            return APIErrorResponse(
                error=error_json.get('error', 'HTTP Error'),
                message=error_json.get('message', 'An error occurred'),
                status_code=http_err.response.status_code
            )
        except Exception as err:
            return APIErrorResponse(
                error='Exception',
                message=f'Other error occurred: {err}'
            )
        return SubmitResponse(**response.json())

    def lab_experiment(self, experiment_ids: List[int]) -> Any:
        """
        Conducts a lab experiment with the given list of experiment IDs.
        Returns:
            LabExperimentResponse: On success.
            APIErrorResponse: On error.
        """
        if not isinstance(experiment_ids, list):
            raise ValueError("experiment_ids should be a list")

        validated_ids = []
        for idx in experiment_ids:
            if not (isinstance(idx, int) or (isinstance(idx, str) and idx.isdigit())):
                raise ValueError("Indexes should be a list of integers or numeric strings")
            validated_ids.append(int(idx))

        url = f"{self.base_url}/lab_experiment"
        headers = {'x-token': self.secret_key}
        response = requests.post(url, json={'ids': validated_ids}, headers=headers)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            error_json = http_err.response.json()
            return APIErrorResponse(
                error=error_json.get('error', 'HTTP Error'),
                message=error_json.get('message', 'An error occurred'),
                status_code=http_err.response.status_code
            )
        except Exception as err:
            return APIErrorResponse(
                error='Exception',
                message=f'Other error occurred: {err}'
            )
        return LabExperimentResponse(**response.json())

    def remained_budget(self) -> Any:
        """
        Fetches the remaining budget from the server.
        Returns:
            RemainedBudgetResponse: On success.
            APIErrorResponse: On error.
        """
        url = f"{self.base_url}/remained_budget"
        headers = {'x-token': self.secret_key}
        response = requests.get(url, headers=headers)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            error_json = http_err.response.json()
            return APIErrorResponse(
                error=error_json.get('error', 'HTTP Error'),
                message=error_json.get('message', 'An error occurred'),
                status_code=http_err.response.status_code
            )
        except Exception as err:
            return APIErrorResponse(
                error='Exception',
                message=f'Other error occurred: {err}'
            )
        return RemainedBudgetResponse(**response.json())

    def requested_ids(self) -> Any:
        """
        Fetches the requested IDs from the server.
        Returns:
            RequestedIDsResponse: On success.
            APIErrorResponse: On error.
        """
        url = f"{self.base_url}/requested_ids"
        headers = {'x-token': self.secret_key}
        response = requests.get(url, headers=headers)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            error_json = http_err.response.json()
            return APIErrorResponse(
                error=error_json.get('error', 'HTTP Error'),
                message=error_json.get('message', 'An error occurred'),
                status_code=http_err.response.status_code
            )
        except Exception as err:
            return APIErrorResponse(
                error='Exception',
                message=f'Other error occurred: {err}'
            )
        return RequestedIDsResponse(**response.json())
