import re
import traceback

from handlers.auth import AgentAuthorizer, AuthPolicy, HttpVerb, UserAuthorizer, validate_token_payload
from handlers.utils import Logger
from settings.aws import (
    AUTHORIZER_TOKEN_IDENTIFIER_DEVICE,
    AUTHORIZER_TOKEN_IDENTIFIER_USER,
)

logs_handler = Logger()
logger = logs_handler.get_logger()


def lambda_handler(event, context):
    logger.info(event)
    logger.info("Client token: " + event["authorizationToken"])
    logger.info("Method ARN: " + event["methodArn"])
    """
    Validate the incoming token and produce the principal user 
    identifier associated with the token this could be accomplished 
    in a number of ways:
    1. Call out to OAuth provider
    2. Decode a JWT token inline
    3. Lookup in a self-managed DB
    """
    principal_id = None
    principal_type = None
    is_token_valid = validate_token_payload(token_payload=event["authorizationToken"])
    if is_token_valid is True:
        token_prefix = event["authorizationToken"].split(" ")[0]
        token_value = event["authorizationToken"].split(" ")[1]
        if token_prefix == AUTHORIZER_TOKEN_IDENTIFIER_DEVICE:
            authorizer = AgentAuthorizer()
            principal_id = token_value
            principal_type = "DEVICE"
        elif token_prefix == AUTHORIZER_TOKEN_IDENTIFIER_USER:
            authorizer = UserAuthorizer()
            principal_id = authorizer.validate_access_token(access_token=token_value)
            principal_type = "USER"
        else:
            logger.error("Wrong prefix in token...")

    if principal_id is None or principal_type is None:
        logger.error(f"Invalid data passed - {principal_id} - {principal_type}")
        raise Exception("Unauthorized")
    else:
        logger.info("Valid data passed...")

    """
    You can send a 401 Unauthorized response to the client by failing like so:
    raise Exception("Unauthorized")

    If the token is valid, a policy must be generated which will allow or deny access to the client,
    if access is denied, the client will receive a 403 Access Denied response,
    if access is allowed, API Gateway will proceed with the backend integration configured 
    on the method that was called
    this function must generate a policy that is associated with the recognized principal user identifier.
    Depending on your use case, you might store policies in a DB, or generate them on the fly 
    keep in mind, the policy is cached for 5 minutes by default (TTL is configurable in the authorizer)
    and will apply to subsequent calls to any method/resource in the RestApi made with the same token.
    """

    """
    The example policy below allows access to all resources in the RestApi
    """
    tmp = event["methodArn"].split(":")
    api_gateway_arn_tmp = tmp[5].split("/")
    aws_account_id = tmp[4]

    policy = AuthPolicy(principal_id, aws_account_id)
    policy.rest_api_id = api_gateway_arn_tmp[0]
    policy.region = tmp[3]
    policy.stage = api_gateway_arn_tmp[1]

    # Finally, build the policy
    # policy.allow_all_methods()
    if principal_type == "USER":
        policy.allow_method(HttpVerb.ALL, "/agents/*")
        policy.allow_method(HttpVerb.ALL, "/keys/*")
    elif principal_type == "DEVICE":
        policy.allow_method(HttpVerb.POST, "/register")
    else:
        policy.deny_all_methods()

    auth_response = policy.build()
    logger.info(auth_response)

    return auth_response


if __name__ == "__main__":
    valid_device_token = "DeviceToken 123"
    valid_user_token = "JWT 123"
    invalid_token = "JWT123"
    response = lambda_handler(
        event={
            "type": "TOKEN",
            "methodArn": "arn:aws:execute-api:us-east-1:112646120612:n8il2c2eic/prod/POST/register",
            "authorizationToken": valid_device_token
        },
        context={},
    )
    logger.info(response)
