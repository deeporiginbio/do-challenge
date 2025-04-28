# DOChallengeClient

## Overview
`DOChallengeClient` is a Python client for interacting with the DO Challenge server. It provides methods for submitting challenge solutions, running lab experiments, and checking the remaining budget.

## Installation
Ensure you have Python installed (>=3.7). You can install the required dependencies using:

```sh
pip install requests
pip install pydantic
```

## Usage

### Initialization
To use `DOChallengeClient`, you need to provide a valid secret key:

```python
from src.client import DOChallengeClient

client = DOChallengeClient(secret_key="your_secret_key")
```

### Submitting Solutions
Submit a list of submission IDs to the server:

```python
response = client.submit([1, 2, 3, 4])
print(response.model_dump_json())
```
**Example Response:**
```json
{
  "available_benchmarks": 1,
  "available_tokens": 99995.0,
  "benchmarks": [0.4, 0.2],
  "best_benchmark_score": 0.4,
  "last_benchmark_score": 0.2,
  "message": "Benchmark completed"
}
```

### Running Lab Experiments
Run experiments using a list of experiment IDs:

```python
response = client.lab_experiment([10, 20, 30])
print(response.model_dump_json())
```
**Example Response:**
```json
{
  "available_tokens": 99995.0,
  "labels": {
    "1": 0.0015035981932025,
    "2": 0.0058774077186091,
    "3": 0.097213482830724,
    "4": 0.0223743568505624,
    "5": 0.017911027138476
  }
}
```

### Checking Remaining Budget
Retrieve the remaining budget from the server:

```python
response = client.remained_budget()
print(response.model_dump_json())
```
**Example Response:**
```json
{
  "available_benchmarks": 2,
  "available_tokens": 99995.0,
  "benchmarks": [4],
}
```

### Getting Requested IDs
Retrieve the Requested IDs from the server:

```python
response = client.requested_ids()
print(response.model_dump_json())
```
**Example Response:**
```json
{
  "available_benchmarks": 2,
  "available_tokens": 99995.0,
  "benchmarks": [4],
}
```

## Error Handling
The client gracefully handles HTTP errors and other exceptions, returning error messages in the response dictionary.

### Common Errors
- **400 Bad Request:** This error occurs when the request is invalid or improperly formatted.
  **Example Response:**
  ```json
  {
    "error": "Bad Request",
    "message": "No benchmarks available",
    "status_code": 400
  }
  ```
  This typically happens when there are no available benchmarks left for the user.

- **403 Forbidden:** If the provided secret key is invalid or unauthorized.
  **Example Response:**
  ```json
  {
    "error": "Forbidden",
    "message": "Invalid secret key",
    "status_code": 403
  }
  ```

- **429 Too Many Requests:** When the rate limit has been exceeded.
  **Example Response:**
  ```json
  {
    "error": "Too Many Requests",
    "message": "100 per 1 minute",
    "status_code": 429
  }
  ```

- **500 Internal Server Error:** If there is an unexpected issue on the server.
  **Example Response:**
  ```json
  {
    "error": "Internal Server Error",
    "message": "An unexpected error occurred",
    "status_code": 500
  }
  ```

- **No Available Tokens:** If the user runs out of tokens and cannot perform further operations.
  **Example Response:**
  ```json
  {
    "error": "Bad Request",
    "message": "Not enough tokens",
    "status_code": 400
  }
  ```
  