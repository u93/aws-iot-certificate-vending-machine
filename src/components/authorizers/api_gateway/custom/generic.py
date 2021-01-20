from components.authorizers.api_gateway.base import BaseApiGwAuthorizer
from handlers.aws import IamAuthPolicyHandler
from handlers.utils import HttpVerb, Logger
from handlers.authorization.schemas import (
    RequestRegistrationAuthorizationSchema,
    RequestRegistrationAuthorizationTokenSchema,
)


project_logger = Logger()
logger = project_logger.get_logger()


class AwsIoTGenericAuthorizer(BaseApiGwAuthorizer):
    class Meta:
        WORKERS = {
            "request_validation_handler": RequestRegistrationAuthorizationSchema,
            "token_validation_handler": RequestRegistrationAuthorizationTokenSchema,
            "token_authorization_handler": None,
            "policy_handler": IamAuthPolicyHandler,
        }

    def __init__(self, authorization_request_data):
        super(AwsIoTGenericAuthorizer, self).__init__(authorization_request_data)

        self.request_validation_handler = self.Meta.WORKERS["request_validation_handler"]()
        self.token_validation_handler = self.Meta.WORKERS["token_validation_handler"]()
        # self.token_authorization_handler = self.Meta.WORKERS["token_authorization_handler"]()
        self.policy_handler = self.Meta.WORKERS["policy_handler"]()

    def validate_request(self):
        """
        Validates the HTTP authorization payload sent by the agent that will be registered.
        :return: Boolean with result of the request validation process.
        """
        validation_errors = self.request_validation_handler.validate(self.authorization_request_data)
        if validation_errors:
            logger.error("Error validating the received payload from the request...")
            self.valid_request_data = False
        else:
            self.valid_request_data = True

        return self.valid_request_data

    def validate_token(self):
        validation_errors = self.token_validation_handler.authorization_token_valid(
            self.authorization_request_data,
            token_length=int(self.configuration_data["DEVICE_AUTHORIZER_TOKEN_PAYLOAD_LENGTH"]),
            token_prefix=self.configuration_data["DEVICE_AUTHORIZER_TOKEN_IDENTIFIER"],
        )
        if validation_errors:
            logger.error("Error validating the received token...")
            self.valid_token_data = False
        else:
            self.valid_token_data = True

        return self.valid_token_data

    def authorize_token(self):
        received_token = self.authorization_request_data["authorizationToken"].split(" ")[1]
        if received_token in self.configuration_data["DEVICE_AUTHORIZER_VALID_TOKENS"]:
            self.authorization_result = True
        else:
            self.authorization_result = False

    def generate_policy(self):
        tmp = self.authorization_request_data["methodArn"].split(":")
        api_gateway_arn_tmp = tmp[5].split("/")
        aws_account_id = tmp[4]
        principal_id = self.authorization_request_data["authorizationToken"].split(" ")[1]

        self.policy_handler.populate(aws_account_id, principal_id)

        self.policy_handler.rest_api_id = api_gateway_arn_tmp[0]
        self.policy_handler.region = tmp[3]
        self.policy_handler.stage = api_gateway_arn_tmp[1]

        if self.valid_request_data is True and self.valid_token_data is True and self.authorization_result is True:
            self.policy_handler.allow_method(HttpVerb.POST, "/register")
        else:
            logger.info(
                f"Denying all methods due to a failure in authoriztion - {self.valid_request_data} - {self.valid_token_data} - {self.authorization_result}"
            )
            self.policy_handler.deny_all_methods()

        generated_policy = self.policy_handler.build()
        return generated_policy
