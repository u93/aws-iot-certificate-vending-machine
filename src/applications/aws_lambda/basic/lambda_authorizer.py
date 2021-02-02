from components.authorizers.api_gateway.custom.generic import AwsIoTGenericAuthorizer
from handlers.utils import Logger

# Import Project Logger
project_logger = Logger()
logger = project_logger.get_logger()

# Set the Authorization Class handler from the import to keep Lambda Code generic.
AUTHORIZER_CLASS = AwsIoTGenericAuthorizer


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
    authorization_handler = AUTHORIZER_CLASS(authorization_request_data=event)
    authorization_response = authorization_handler.execute()

    logger.info(authorization_response)
    return authorization_response
