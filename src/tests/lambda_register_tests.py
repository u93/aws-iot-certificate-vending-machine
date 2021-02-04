import json
import random
import os
import string

os.environ["APP_CONFIG_PATH"] = "/multa-cvm/dev/config-parameters"

from handlers.utils import Logger
from applications.aws_lambda.basic.lambda_register import lambda_handler as register_handler

# Import Project Logger
project_logger = Logger()
logger = project_logger.get_logger()


def generate_thing_name():
    """Returns a common thing name to use across tests."""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(10))


def test_incorrect_payload():
    """Tests incorrect payload received by Lambda"""
    event = {"httpMethod": "POST", "body": "{}"}

    assert isinstance(event, dict)
    assert event["httpMethod"] == "POST"
    assert isinstance(event["body"], str)
    assert isinstance(json.loads(event["body"]), dict)

    result = register_handler(event=event, context={})

    assert isinstance(result, dict)
    assert isinstance(result["statusCode"], int)
    assert result["statusCode"] == 500
    assert isinstance(json.loads(result["body"]), dict)
    assert isinstance(json.loads(result["body"])["error"], str)
    assert json.loads(result["body"])["error"] == "Uncaught error..."


def test_correct_thing_registration():
    """Tests correct payload received by Lambda"""
    event = {"httpMethod": "POST", "body": {"thingName": generate_thing_name(), "version": "1"}}
    event["body"] = json.dumps(event["body"])

    assert isinstance(event, dict)
    assert event["httpMethod"] == "POST"
    assert isinstance(event["body"], str)
    assert isinstance(json.loads(event["body"]), dict)

    result = register_handler(event=event, context={})

    assert isinstance(result, dict)
    assert isinstance(result["statusCode"], int)
    assert result["statusCode"] == 200
    assert isinstance(json.loads(result["body"]), dict)
    assert isinstance(json.loads(result["body"])["certificateData"], dict)
    assert isinstance(json.loads(result["body"])["rootCa"], str)


def test_thing_registration_double():
    """Tests event in case that AWS IoT Thing tries to register twice"""
    event = {"httpMethod": "POST", "body": {"thingName": generate_thing_name(), "version": "1"}}
    event["body"] = json.dumps(event["body"])

    assert isinstance(event, dict)
    assert event["httpMethod"] == "POST"
    assert isinstance(event["body"], str)
    assert isinstance(json.loads(event["body"]), dict)

    result = register_handler(event=event, context={})

    assert isinstance(result, dict)
    assert isinstance(result["statusCode"], int)
    assert result["statusCode"] == 200
    assert isinstance(json.loads(result["body"]), dict)
    assert isinstance(json.loads(result["body"])["certificateData"], dict)
    assert isinstance(json.loads(result["body"])["rootCa"], str)

    result = register_handler(event=event, context={})

    assert isinstance(result, dict)
    assert isinstance(result["statusCode"], int)
    assert result["statusCode"] == 400
    assert isinstance(json.loads(result["body"]), dict)
    assert isinstance(json.loads(result["body"])["status"], bool)
    assert json.loads(result["body"])["status"] is False
    assert json.loads(result["body"])["error"] == "Thing exists in the AWS IoT Account, exiting..."
