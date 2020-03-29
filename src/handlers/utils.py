import json
import logging
import os

from marshmallow import Schema, fields, validates, ValidationError


def base_response(status_code: int, dict_body: dict):
    headers = {"Content-Type": "application/json"}
    response = dict(statusCode=status_code, headers=headers, body=json.dumps(dict_body))
    return response


class RegisterThingSchema(Schema):
    thing_name = fields.Str(required=True, data_key="thingName")
    thing_type_name = fields.Str(required=True, data_key="thingTypeName")
    attribute_payload = fields.Dict(attributes=fields.Dict(), data_key="thingAttributes")

    # @validates("thing_type_name")
    # def thing_type_exists(self, value):
    #     # TODO: AT INIT, THE DEFAULT THING TYPES MUST BE CREATED OR LATER UPDATED BY CLI COMMAND
    #     if value not in thing_types:
    #         raise ValidationError("Thing type does not exists!")


class Logger:
    def __init__(self):
        console_format = "%(pathname)s - %(levelname)s - %(funcName)s - %(lineno)d - %(message)s"
        root = logging.getLogger()
        if root.handlers:
            for handler in root.handlers:
                root.removeHandler(handler)
        logging.basicConfig(format=console_format, level=os.environ.get("LOG_LEVEL", "INFO"))
        self.logger = logging.getLogger()

    def get_logger(self):
        return self.logger
