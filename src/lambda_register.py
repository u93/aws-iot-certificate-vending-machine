import json
import time
import traceback

from components.registrators.aws_iot.generic import AwsIoTGenericRegistrator
from handlers.utils import Logger, base_response

# Import Project Logger
project_logger = Logger()
logger = project_logger.get_logger()

# Set the Registration Class handler from the import to keep Lambda Code generic.
REGISTRATION_CLASS = AwsIoTGenericRegistrator


def lambda_handler(event, context):
    logger.info(event)

    http_method = event["httpMethod"]

    # Ping Pong method to validate API.
    if http_method == "GET":
        return base_response(status_code=200, dict_body={"response": True, "time": round(time.time())})

    if http_method == "POST":
        try:
            request_body = json.loads(event["body"])

            registration_handler = REGISTRATION_CLASS(device_request_data=request_body)
            registration_code, registration_response = registration_handler.execute()

            return base_response(status_code=registration_code, dict_body=registration_response)

        except Exception:
            logger.error("Uncaught error...")
            logger.error(traceback.format_exc())

            return base_response(status_code=500, dict_body={"error": "Uncaught error..."})

    else:
        return base_response(status_code=405)


if __name__ == "__main__":
    fake_wrong_lambda_event = {
        "httpMethod": "POST",
        "body": "{}"
    }
    fake_lambda_event = {
        "httpMethod": "POST",
        "body": '{"thingName":"Test","version":"1"}'
    }
    response = lambda_handler(event=fake_lambda_event, context={})
