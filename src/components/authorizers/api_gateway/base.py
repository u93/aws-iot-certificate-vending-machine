from handlers.aws import ConfigurationHandler
from settings.aws import APP_CONFIG_PATH
from handlers.utils import Logger


logs_handler = Logger()
logger = logs_handler.get_logger()


class BaseApiGwAuthorizer:
    class Meta:
        """
        Define the Worker Classes for the base steps in the authorization process.
        """

        WORKERS = {
            "request_validation_handler": None,
            "token_validation_handler": None,
            "token_authorization_handler": None,
            "policy_handler": None,
        }

    def __init__(self, authorization_request_data: dict, *args, **kwargs):
        self.configuration_handler = None
        self.configuration_data = self.get_configuration()

        self.authorization_request_data = authorization_request_data

        self.valid_request_data = None
        self.valid_token_data = None
        self.token_authorization_handler = None

        self.authorization_result = None

    def execute(self):
        """
        Executes flow of device registration request authorization.
        :return: API Gateway Policy.
        """
        self.validate_request()
        self.validate_token()

        self.authorize_token()

        authorization_policy = self.generate_policy()

        return authorization_policy

    def validate_request(self, **kwargs):
        raise NotImplementedError

    def validate_token(self, **kwargs):
        raise NotImplementedError

    def authorize_token(self, **kwargs):
        raise NotImplementedError

    def generate_policy(self, **kwargs):
        raise NotImplementedError

    def get_configuration(self):
        """
        Gets the application configuration from SSM Parameter Store.
        :return: Configuration data dictionary.
        """
        self.configuration_handler = ConfigurationHandler(path=APP_CONFIG_PATH)
        configuration_data = self.configuration_handler.get_config()

        return configuration_data
