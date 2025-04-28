from flask import jsonify

from app.config.core.logger import logger


def json_error_handler(error, status_code, error_name):
    """ Helper function to format error responses in JSON """
    response = jsonify({"error": error_name, "message": error.description})
    response.status_code = status_code
    return response

def internal_server_error(e):
    logger.error("Unhandled Exception occurred", exc_info=True)
    response = jsonify({"error": "Internal Server Error", "message": str(e)})
    response.status_code = 500
    return response