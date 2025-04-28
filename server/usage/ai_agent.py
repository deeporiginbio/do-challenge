import json
import logging
import requests


class ChatAssistant:
    def __init__(self, client):
        self.client = client
        self.model = "gpt-4o"
        self.api_host = "http://10.5.0.204:5000/api"  # Centralized API host for all endpoints

        # Define tool signatures with updated descriptions
        self.tool_signatures = [
            {
                "type": "function",
                "function": {
                    "name": "get_labels",
                    "description": "Fetch labels using a secret key and a list of indexes. Checks available tokens before calling.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "secret_key": {
                                "type": "string",
                                "description": "The secret key for authentication."
                            },
                            "indexes": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "A list of indexes to fetch labels for."
                            }
                        },
                        "required": ["secret_key", "indexes"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "benchmark",
                    "description": "Call the benchmark API with exactly 2000 indexes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "secret_key": {
                                "type": "string",
                                "description": "The secret key for authentication."
                            },
                            "indexes": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "A list of exactly 2000 indexes for benchmarking. Make sure to validate the length."
                            }
                        },
                        "required": ["secret_key", "indexes"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "available_tokens",
                    "description": "Fetch the number of available tokens from the API endpoint.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "secret_key": {
                                "type": "string",
                                "description": "The secret key for authentication."
                            }
                        },
                        "required": ["secret_key"]
                    }
                }
            }
        ]

    def handle_tool_call(self, function_name, args):
        """
        Process a tool call and return the result.
        """
        tool_name = function_name
        try:
            tool_args = json.loads(args)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON arguments: {args}")
            return f"Error: Invalid JSON arguments - {e}"

        logging.info(f"Handling tool call: {tool_name} with args: {tool_args}")
        print(f"Handling tool call: {tool_name} with args: {tool_args}")

        if tool_name == "get_labels":
            return self.perform_get_labels(tool_args["secret_key"], tool_args["indexes"])
        elif tool_name == "benchmark":
            return self.perform_benchmark(tool_args["secret_key"], tool_args["indexes"])
        elif tool_name == "available_tokens":
            return self.perform_available_tokens(tool_args["secret_key"])

        logging.warning(f"Unknown tool call: {tool_name}")
        return f"Unknown tool call: {tool_name}"

    def perform_get_labels(self, secret_key, indexes):
        """
        Call the get_labels API endpoint after checking available tokens.
        """
        # Check available tokens before requesting labels
        available = json.loads(self.perform_available_tokens(secret_key))
        # ["available_tokens"]
        try:
            available_tokens = int(available[0]["available_tokens"])
        except ValueError:
            logging.error("Failed to parse available tokens")
            return f"Error: Failed to parse available tokens: {available}"

        if available_tokens < len(indexes):
            error_msg = f"Not enough tokens. Required: {len(indexes)}, Available: {available_tokens}"
            logging.error(error_msg)
            return error_msg

        url = f"{self.api_host}/get_labels"
        headers = {"x-token": secret_key}
        body = {"challenge_name": "DO2025", "indexes": indexes}
        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            logging.info("Successfully fetched labels")
            return response.text
        except requests.RequestException as e:
            logging.error(f"Error in perform_get_labels: {e}")
            return f"Error fetching labels: {e}"

    def perform_available_tokens(self, secret_key):
        """
        Call the available tokens API endpoint.
        """
        url = f"{self.api_host}/available_tokens"
        headers = {"x-token": secret_key}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            logging.info("Successfully fetched available tokens")
            return response.text.strip()
        except requests.RequestException as e:
            logging.error(f"Error in perform_available_tokens: {e}")
            return f"Error fetching tokens: {e}"

    def perform_benchmark(self, secret_key, indexes):
        """
        Call the benchmark API endpoint. Requires exactly 2000 indexes.
        """
        if len(indexes) != 2000:
            error_msg = "Error: Invalid number of indexes for benchmark. Expected 2000 indexes."
            logging.error(error_msg)
            return error_msg

        url = f"{self.api_host}/benchmark"
        headers = {"x-token": secret_key}
        body = {"challenge_name": "DO2025", "indexes": indexes}
        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            logging.info("Successfully called benchmark")
            return response.text
        except requests.RequestException as e:
            logging.error(f"Error in perform_benchmark: {e}")
            return f"Error in benchmark: {e}"

    def perform_submit_predictions(self, secret_key, predictions):
        """
        Call the submit predictions API endpoint. Predictions must be exactly 2000.
        """
        if len(predictions) != 2000:
            error_msg = "Error: Invalid number of predictions. Expected exactly 2000."
            logging.error(error_msg)
            return error_msg

        url = f"{self.api_host}/submit"
        headers = {"x-token": secret_key}
        body = {"predictions": predictions}
        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            logging.info("Successfully submitted predictions")
            return response.text
        except requests.RequestException as e:
            logging.error(f"Error in perform_submit_predictions: {e}")
            return f"Error submitting predictions: {e}"

    def chat_loop(self, messages, temperature=1):
        """
        Continuously call the completions API while handling tool calls.
        """
        while True:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tool_signatures,
                    temperature=temperature,
                )
            except Exception as e:
                logging.error(f"Error during chat completion: {e}")
                break

            logging.info("Received response from completions API")
            choice = response.choices[0]
            messages.append(choice.message)

            # Process any tool calls, if present
            if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    tool_result = self.handle_tool_call(tool_call.function.name, tool_call.function.arguments)
                    print(f"Tool call: {tool_call.function.name} result: {tool_result}")
                    messages.append({
                        "role": "tool",
                        "content": tool_result,
                        "tool_call_id": tool_call.id
                    })
            else:
                # Final response without tool calls ends the loop
                print("Final response:", choice.message.content)


if __name__ == "__main__":
    from openai import OpenAI

    logging.basicConfig(level=logging.INFO)

    client = OpenAI()
    assistant = ChatAssistant(client)

    # System message with the challenge description and API guidelines
    system_message = {
        "role": "system",
        "content": """
# DO 2025 Challenge - AI Agent Task Description

YOUR_SECRET_KEY are c-8ZAi_6N5GfgNaSZtKdoR5CrlOqpseM_dUyv1EMaEM=
## Overview  
You are an autonomous OpenAI agent participating in the **DO 2025 Challenge**. Your goal is to process label data, generate evaluation IDs using your internal completions capabilities, and submit predictions via the benchmark API.

## API Host & Authentication  
All API endpoints are hosted at: **http://localhost:5000/api**  

### Authentication  
- Every API request **must** include a secret key in the request headers.  
- Set the secret key in the `X-Token` header as follows:  
  ```
  X-Token: YOUR_SECRET_KEY
  ```

## Task Steps  

### 1. Retrieve Labels  
- **API Call:**  
  ```http
  GET http://localhost:5000/api/get_labels
  ```
- **Headers:**  
  ```http
  X-Token: YOUR_SECRET_KEY
  ```
- **Token Cost:** Each label request costs **1 token** from your **10,000-token** budget.  
- **Validation:** Ensure the API response is valid (check status codes and data integrity).  
- **Extraction:** Parse the response and extract the necessary labels.  

You can get labels for up to **10,000 indexes** in a single request. You must call 2000 indexes at a time.
You can get labels in random order not just sequential order.
You must check the available tokens before making label requests.

### 2. Check Available Tokens  
- **API Call:**  
  ```http
  GET http://localhost:5000/api/available_tokens
  ```
- **Headers:**  
  ```http
  X-Token: YOUR_SECRET_KEY
  ```
- **Strategy:** Optimize label requests to stay within your **10,000-token** limit.  

### 3. Generate Evaluation IDs (Internal Completions)  
- **Processing:** Based on the retrieved labels, generate predictions for evaluation IDs using internal completions logic. 
- **Constraints:** You **must not** use external completion API calls.  
- **Output Format:** Ensure that the predicted IDs match the expected format.  
- **Submission Length:** The final submission must contain exactly **2,000 indexes**.
You can generate submission indexes in random or some logical order not just sequential order.

### 4. Submit Predictions  
Submit 2000 labels if you have them. If you don't have 2000 labels, you can not submit. So do not try it.
- **API Call:**  
  ```http
  POST http://localhost:5000/api/submit
  ```
- **Headers:**  
  ```http
  X-Token: YOUR_SECRET_KEY
  ```
- **Payload Format:**  
  ```json
  {
    "predictions": [id1, id2, ..., id2000]
  }
  ```
- **Error Handling:** Handle and log any errors or unsuccessful responses.

## Benchmarks  
There are **three** available benchmarks for evaluation. Your performance will be assessed based on prediction accuracy and token efficiency.
From benchmark you must generate 2000 indexes and submit them to the benchmark API.

## Execution Guidelines  
- **API Host:** All API calls must be made to **http://localhost:5000/api**.  
- **Authentication:** Every request **must** include the secret key in the `X-Token` header.  
- **Budget Management:** You have a **10,000-token limit**; each label request costs **1 token**.  
- **Token Monitoring:** Use `GET http://localhost:5000/api/available_tokens` to track remaining tokens.  
- **Workflow:** Follow this structured process: **Retrieve Labels → Generate IDs → Submit Predictions**.  
- **Submission Size:** Your submission must contain exactly **2,000 indexes**.  
- **Logging & Debugging:** Implement error handling and log key steps.  
- **Challenge Rules:** Adhere to format specifications and challenge constraints.

Your performance in the **DO 2025 Challenge** depends on precise label retrieval, efficient token usage, and accurate evaluation ID predictions.  
Execute each step carefully to maximize success.
        """
    }

    messages = [
        system_message,
        {"role": "user",
         "content": "Please solve the task, retrieve labels using 1000 indexes, and submit predictions only with 2000 indexes."}
    ]

    assistant.chat_loop(messages)
