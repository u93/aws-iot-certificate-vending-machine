from handlers.utils import Logger
from applications.aws_lambda.basic.lambda_authorizer import lambda_handler as auth_handler


# Import Project Logger
project_logger = Logger()
logger = project_logger.get_logger()

valid_device_token = "DeviceToken NjWO2tVh6fVAeNuLwRsPi-c6N7SP5-DT"
invalid_device_token = "DeviceToken 123"
invalid_token_prefix = "Token 123"
invalid_token_composition = "DeviceToken-123"

response = auth_handler(
    event={
        "type": "TOKEN",
        "methodArn": "arn:aws:execute-api:us-east-1:112646120612:n8il2c2eic/prod/POST/register",
        "authorizationToken": valid_device_token,
    },
    context={},
)
logger.info(response)
