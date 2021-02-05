import json
import os

os.environ["APP_CONFIG_PATH"] = "/multa-cvm/dev/config-parameters"

from handlers.utils import Logger
from applications.aws_lambda.basic.lambda_authorizer import lambda_handler as auth_handler


# Import Project Logger
project_logger = Logger()
logger = project_logger.get_logger()

valid_device_token = "DeviceToken NjWO2tVh6fVAeNuLwRsPi-c6N7SP5-DT"
invalid_device_token = "DeviceToken 123"
invalid_token_prefix = "Token 123"
invalid_token_composition = "DeviceToken-123"


def test_valid_device_token():
    """Tests correct payload received by Authorizer Lambda"""
    token = "DeviceToken NjWO2tVh6fVAeNuLwRsPi-c6N7SP5-DT"
    event = {
        "type": "TOKEN",
        "methodArn": "arn:aws:execute-api:us-east-1:112646120612:n8il2c2eic/prod/POST/register",
        "authorizationToken": token,
    }

    assert isinstance(event, dict)
    assert event["type"] == "TOKEN"
    assert isinstance(event["methodArn"], str)
    assert isinstance(event["authorizationToken"], str)

    result = auth_handler(event=event, context={})

    assert isinstance(result, dict)
    assert isinstance(result["principalId"], str)
    assert result["principalId"] == "".join(token.split(" "))
    assert isinstance(result["policyDocument"], dict)

    assert isinstance(result["policyDocument"]["Version"], str)
    assert result["policyDocument"]["Version"] == "2012-10-17"

    assert isinstance(result["policyDocument"]["Statement"], list)
    for element in result["policyDocument"]["Statement"]:
        assert element["Action"] == "execute-api:Invoke"
        assert element["Effect"] == "Allow"
        assert isinstance(element["Resource"], list)
        for sub_element in element["Resource"]:
            assert isinstance(sub_element, str)
            assert "POST" in sub_element
            assert "register" in sub_element


def test_invalid_device_token():
    """Tests invalid device token value received by Authorizer Lambda"""
    token = "DeviceToken 123"
    event = {
        "type": "TOKEN",
        "methodArn": "arn:aws:execute-api:us-east-1:112646120612:n8il2c2eic/prod/POST/register",
        "authorizationToken": token,
    }

    assert isinstance(event, dict)
    assert event["type"] == "TOKEN"
    assert isinstance(event["methodArn"], str)
    assert isinstance(event["authorizationToken"], str)

    result = auth_handler(event=event, context={})

    assert isinstance(result, dict)
    assert isinstance(result["principalId"], str)
    assert result["principalId"] == "".join(token.split(" "))
    assert isinstance(result["policyDocument"], dict)

    assert isinstance(result["policyDocument"]["Version"], str)
    assert result["policyDocument"]["Version"] == "2012-10-17"

    assert isinstance(result["policyDocument"]["Statement"], list)
    for element in result["policyDocument"]["Statement"]:
        assert element["Action"] == "execute-api:Invoke"
        assert element["Effect"] == "Deny"
        assert isinstance(element["Resource"], list)
        for sub_element in element["Resource"]:
            assert isinstance(sub_element, str)
            assert "*" in sub_element
            assert "*" in sub_element


def test_invalid_token_prefix():
    """Tests invalid token prefix received by Authorizer Lambda"""
    token = "Token 123"
    event = {
        "type": "TOKEN",
        "methodArn": "arn:aws:execute-api:us-east-1:112646120612:n8il2c2eic/prod/POST/register",
        "authorizationToken": token,
    }

    assert isinstance(event, dict)
    assert event["type"] == "TOKEN"
    assert isinstance(event["methodArn"], str)
    assert isinstance(event["authorizationToken"], str)

    result = auth_handler(event=event, context={})

    assert isinstance(result, dict)
    assert isinstance(result["principalId"], str)
    assert result["principalId"] == "".join(token.split(" "))
    assert isinstance(result["policyDocument"], dict)

    assert isinstance(result["policyDocument"]["Version"], str)
    assert result["policyDocument"]["Version"] == "2012-10-17"

    assert isinstance(result["policyDocument"]["Statement"], list)
    for element in result["policyDocument"]["Statement"]:
        assert element["Action"] == "execute-api:Invoke"
        assert element["Effect"] == "Deny"
        assert isinstance(element["Resource"], list)
        for sub_element in element["Resource"]:
            assert isinstance(sub_element, str)
            assert "*" in sub_element
            assert "*" in sub_element


def test_invalid_token_composition():
    """Tests invalid token composition received by Authorizer Lambda"""
    token = "DeviceToken-123"
    event = {
        "type": "TOKEN",
        "methodArn": "arn:aws:execute-api:us-east-1:112646120612:n8il2c2eic/prod/POST/register",
        "authorizationToken": token,
    }

    assert isinstance(event, dict)
    assert event["type"] == "TOKEN"
    assert isinstance(event["methodArn"], str)
    assert isinstance(event["authorizationToken"], str)

    result = auth_handler(event=event, context={})

    assert isinstance(result, dict)
    assert isinstance(result["principalId"], str)
    assert result["principalId"] == "".join(token)
    assert isinstance(result["policyDocument"], dict)

    assert isinstance(result["policyDocument"]["Version"], str)
    assert result["policyDocument"]["Version"] == "2012-10-17"

    assert isinstance(result["policyDocument"]["Statement"], list)
    for element in result["policyDocument"]["Statement"]:
        assert element["Action"] == "execute-api:Invoke"
        assert element["Effect"] == "Deny"
        assert isinstance(element["Resource"], list)
        for sub_element in element["Resource"]:
            assert isinstance(sub_element, str)
            assert "*" in sub_element
            assert "*" in sub_element
