import json
import logging
import os

from marshmallow import Schema, fields, validates, ValidationError


def base_response(status_code: int, dict_body=None):
    headers = {"Content-Type": "application/json"}
    response_dict = dict(statusCode=status_code, headers=headers)
    if dict_body is not None and isinstance(dict_body, dict):
        response_dict["body"] = json.dumps(dict_body)

    return response_dict


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
