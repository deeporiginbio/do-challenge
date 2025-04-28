import os
import time

from dotenv import load_dotenv
from werkzeug.exceptions import (
    NotFound, BadRequest, Unauthorized, Forbidden,
    MethodNotAllowed, TooManyRequests, InternalServerError
)

from flask import Flask, request, g
from app.routes.main import main_blueprint
from app.routes.teams import teams_blueprint
from app.routes.challanges import challenges_blueprint
from app.routes.tasks import tasks_blueprint
from app.routes.error_handler import json_error_handler, internal_server_error
from app.config.core.logger import logger
from flasgger import Swagger
from flask_limiter import Limiter
from flask_cors import CORS
from app.models.db import create_mongo_connection

app = Flask(__name__)

# Initialize Swagger
app.config['SWAGGER'] = {
    'title': 'Competition API',
    'uiversion': 3
}
swagger = Swagger(app)

def get_token():
    return request.headers.get("X-TOKEN", "anonymous")

limiter = Limiter(app=app, key_func=get_token, default_limits=["100 per minute"])

CORS(app,
     supports_credentials=True,
     resources={r"/*": {"origins": "*"}},
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "X-API-KEY", "X-TOKEN"])

# Register blueprints
app.register_blueprint(main_blueprint, url_prefix='/api')
app.register_blueprint(teams_blueprint, url_prefix='/api/teams')
app.register_blueprint(challenges_blueprint, url_prefix='/api/challenges')
app.register_blueprint(tasks_blueprint, url_prefix='/api/tasks')

# Error Handlers
app.register_error_handler(BadRequest, lambda e: json_error_handler(e, 400, "Bad Request"))
app.register_error_handler(Unauthorized, lambda e: json_error_handler(e, 401, "Unauthorized"))
app.register_error_handler(Forbidden, lambda e: json_error_handler(e, 403, "Forbidden"))
app.register_error_handler(NotFound, lambda e: json_error_handler(e, 404, "Not Found"))
app.register_error_handler(MethodNotAllowed, lambda e: json_error_handler(e, 405, "Method Not Allowed"))
app.register_error_handler(TooManyRequests, lambda e: json_error_handler(e, 429, "Too Many Requests"))
app.register_error_handler(InternalServerError, lambda e: json_error_handler(e, 500, "Internal Server Error"))
app.register_error_handler(Exception, lambda e: internal_server_error(e))

create_mongo_connection()


# ---------------- REQUEST LOGGING ----------------
@app.before_request
def log_request_info():
    """Log incoming request details in a structured and user-friendly format."""
    if request.method == "OPTIONS":
        return

    g.start_time = time.time()

    x_token = request.headers.get("X-Token", "N/A")  # Get X-Token if available

    log_message = f"[REQUEST] {request.method} {request.url} | IP: {request.remote_addr} | X-Token: {x_token}"
    logger.info(log_message)

    if request.method in ["POST", "PUT", "PATCH"]:
        body = request.get_data(as_text=True).strip()
        if body:
            if len(body) > 500:
                body = f"{body[:100]} ... {body[-100:]}"
            logger.info(f"[REQUEST BODY] {body}")

@app.before_request
def handle_options():
    """Handle preflight requests for CORS."""
    if request.method == "OPTIONS":
        return "", 204


@app.after_request
def log_response_info(response):
    """Log response details, including errors for 4xx/5xx responses, but ignore OPTIONS."""
    if request.method == "OPTIONS" or response.status_code == 308:
        return response

    execution_time = (time.time() - g.start_time) * 1000 if hasattr(g, "start_time") else None
    log_message = (
        f"[RESPONSE] {response.status_code} {request.method} {request.url} | "
        f"Time: {execution_time:.2f}ms" if execution_time else "[RESPONSE] start_time not set"
    )

    x_token = request.headers.get("X-Token", "N/A")
    if response.status_code >= 400:
        logger.error(
            f"[ERROR] {response.status_code} - {request.method} {request.url} | X-Token: {x_token} | {response.get_data(as_text=True)}")

    logger.info(log_message)

    if response.content_length and response.content_length < 500:
        logger.info(f"[RESPONSE BODY] {response.get_data(as_text=True)}")

    return response

# ---------------- START APP ----------------
if __name__ == '__main__':
    create_mongo_connection()
    app.run(debug=True)
