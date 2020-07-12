import json
import time

from handlers.utils import Logger, base_response

project_logger = Logger()
logger = project_logger.get_logger()


def lambda_handler(event, context):
    logger.info(event)
    logger.info(event["httpMethod"])
    logger.info(event["queryStringParameters"])
    logger.info(event["multiValueQueryStringParameters"])
    logger.info(event["pathParameters"])
    logger.info(event["body"])

    http_method = event["httpMethod"]
    if http_method == "GET":
        return base_response(status_code=200, dict_body=event)

    elif http_method == "POST":
        return base_response(status_code=200, dict_body=event)

    elif http_method == "DELETE":
        return base_response(status_code=200, dict_body=event)

    else:
        return base_response(status_code=200, dict_body={"error": f"Unhandled method... - {event['httpMethod']}"})