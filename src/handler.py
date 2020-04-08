import json
import time

from handlers.aws import ThingHandlers
from handlers.registration import CvmRegistration
from handlers.utils import RegisterThingSchema, Logger, base_response
from settings.app import THING_TYPE_NAME_RULE

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
        request_body = json.loads(event["body"])
        thing_handler = ThingHandlers()

        logger.info("Enriching thing data before creation")
        thing_attributes = dict(creation_date=round(time.time()), multa_agent_version=request_body.pop("version", "-"))
        thing_type = thing_handler.get_thing_type(partial_name=THING_TYPE_NAME_RULE)
        request_body["thingTypeName"] = thing_type
        request_body["thingAttributes"]["attributes"] = thing_attributes

        # Validating if request has valid parameters
        register_thing_schema = RegisterThingSchema()
        errors = register_thing_schema.validate(request_body)
        if errors:
            return base_response(status_code=400, dict_body={"message": str(errors), "failureCode": "3"})

        # Registering IoT Thing in AWS IoT
        thing_handler = CvmRegistration(thing_data=request_body)
        registration_response, registration_code = thing_handler.register_thing()
        if registration_response is False:
            return base_response(status_code=500, dict_body={"message": "Unable to register thing", "failureCode": registration_code})
        response = {
            "certificates": registration_response["certificate_data"],
            "rootCA": registration_response["root_ca"],
            "failureCode": registration_code
        }
        return base_response(status_code=200, dict_body=response)

    if http_method == "DELETE":
        logger.info("Deleting AWS IoT Thing...")
        return base_response(status_code=204)
