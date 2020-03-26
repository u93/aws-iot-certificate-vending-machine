import json
import logging


def lambda_handler(event, context):
    logging.info(event)
    response = {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"test": "OK"})}
    return response
