import json

from .handlers.registration import CvmRegistration
from .handlers.utils import RegisterThingSchema, Logger, base_response

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
        return base_response(status_code=200, dict_body={"response": "OK"})

    if http_method == "POST":
        logger.info(json.loads(event["body"]))

        register_thing_schema = RegisterThingSchema()
        # Validating if request has valid parameters
        request_body = json.loads(event["body"])
        errors = register_thing_schema.validate(request_body)
        if errors:
            return base_response(status_code=400, dict_body={"message": str(errors)})

        # Registering IoT Thing in AWS IoT
        thing_handler = CvmRegistration(thing_data=request_body)
        registration_response = thing_handler.register_thing()
        if registration_response is False:
            return base_response(status_code=500, dict_body={"message": "Unable to register thing"})
        response = {
            "certificates": registration_response["certificate_data"],
            "rootCA": registration_response["root_ca"],
        }
        return base_response(status_code=200, dict_body=response)
