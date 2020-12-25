import json
import time
import traceback

from components.registrators.aws_iot.generic import AwsIoTGenericRegistrator
from handlers.utils import Logger, base_response

project_logger = Logger()
logger = project_logger.get_logger()


def lambda_handler(event, context):
    logger.info(event)

    http_method = event["httpMethod"]

    if http_method == "GET":
        return base_response(status_code=200, dict_body={"response": "OK"})

    if http_method == "POST":
        try:
            request_body = json.loads(event["body"])

            registration_handler = AwsIoTGenericRegistrator(device_request_data=request_body)

            registration_handler.validate_request()
            registration_handler.transform_request()

            registration_handler.register()

            registration_response = registration_handler.generate_response()

            return base_response(status_code=200, dict_body=registration_response)

        except Exception:
            logger.error("Uncaught error...")
            logger.error(traceback.format_exc())

            return base_response(status_code=400, dict_body={"error": "Uncaught error..."})

    else:
        return base_response(status_code=405)


if __name__ == "__main__":
    fake_wrong_lambda_event = {
        "httpMethod": "POST",
        "body": "{}"
    }
    fake_lamda_event = {}
    response = lambda_handler(event=fake_wrong_lambda_event, context={})
