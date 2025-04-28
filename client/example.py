import random
from src.client import DOChallengeClient


def main():
    # Create a client object, MODIFY THE SECRET KEY
    SECRET_KEY = "<SECRET_KEY>"
    client = DOChallengeClient(SECRET_KEY)

    # Call the remained_budget method
    print("\n" + "-" * 10 + " REMAINING BUDGET " + "-" * 10 + "\n")
    remaining_budget_response = client.remained_budget()
    if hasattr(remaining_budget_response, "error"):
        print(remaining_budget_response.error, " : ", remaining_budget_response.message)
    else:
        print(f"Available benchmarks: {remaining_budget_response.available_benchmarks}")
        print(f"Available Tokens: {remaining_budget_response.available_tokens}")
        print(f"Benchmarks: {remaining_budget_response.benchmarks}")


    # Call the requested_ids method
    print("\n" + "-" * 10 + " REQUESTED IDS " + "-" * 10 + "\n")
    requested_ids_response = client.requested_ids()
    if hasattr(requested_ids_response, "error"):
        print(requested_ids_response.error, " : ", requested_ids_response.message)
    else:
        requested_ids = requested_ids_response.requested_ids
        compressed_ids = str(requested_ids[:3] + ["..."] + requested_ids[-3:]) if len(requested_ids) > 10 else str(requested_ids)
        print(f"Requested IDs:(Please adjust for more visibilty): {compressed_ids}")

    # Call the lab_experiment method
    print("\n" + "-" * 10 + " LAB EXPERIMENT " + "-" * 10 + "\n")
    raise Exception("This is an exception for protection random lab experiment please adjust the code")
    lab_exp_response = client.lab_experiment([1])
    if hasattr(lab_exp_response, "error"):
        print(lab_exp_response.error, " : ", lab_exp_response.message)
    else:
        print(f"Available tokens: {lab_exp_response.available_tokens}")
        print(f"Labels: {lab_exp_response.labels}")
    
    # Call the submit method
    print("\n" + "-" * 10 + " SUBMISSION " + "-" * 10 + "\n")
    raise Exception("This is an exception for protection random submissionm please adjust the code")
    # Note that length must be 3000
    submission_response = client.submit([random.choice(range(1000000)) for i in range(5000)])
    if hasattr(submission_response, "error"):
        print(submission_response.error, " : ", submission_response.message)
    else:
        print(f"Avaialble benchmarks: {submission_response.available_benchmarks}")
        print(f"Available tokens: {submission_response.available_tokens}")
        print(f"Benchmarks: {submission_response.benchmarks}")
        print(f"Best Benchmark Score: {submission_response.best_benchmark_score}")
        print(f"Last Benchmark Score: {submission_response.last_benchmark_score}")

if __name__ == '__main__':
    main()