from handlers.aws import ConfigurationHandler
from settings.aws import APP_CONFIG_PATH


class BaseRegistrator:
    class Meta:
        """
        Define the Worker Classes for the base steps in the registration process.
        """
        WORKERS = {
            "request_validation_handler": None,
            "registration_validation_handler": None,
            "thing_handler": None
        }

    def __init__(self, device_request_data: dict, **kwargs):
        self.configuration_handler = None
        self.configuration_data = self.get_configuration()

        self.device_request_data = device_request_data
        self.device_registration_data = dict()
        self.valid_request_data = None
        self.valid_registration_data = None
        self.registration_result = None
        self.error = None
        self.code = None

    def execute(self):
        """
        Executes flow of device registration.
        :return: Registration Code (HTTP Code) that will be used in response; Response dictionary that will be returned
        to the agent executing the registration request.
        """
        self.validate_request()
        self.transform_request()

        self.register()

        registration_code, registration_response = self.generate_response()

        return registration_code, registration_response

    def validate_request(self, **kwargs):
        raise NotImplementedError

    def transform_request(self, **kwargs):
        raise NotImplementedError

    def register(self, **kwargs):
        raise NotImplementedError

    def generate_response(self) -> tuple:
        """
        Generates the response that will contain the HTTP Response CODE and the HTTP Response Body.
        :return: HTTP Response Code; HTTP Response Body.
        """
        if self.registration_result is False:
            response = {
                "status": self.registration_result,
                "error": self.error
            }
        else:
            response = {
                "certificateData": self.registration_result["certificate_data"],
                "rootCa": self.registration_result["root_ca"]
            }

        return self.code, response

    def get_configuration(self):
        """
        Gets the application configuration from SSM Parameter Store.
        :return: Configuration data dictionary.
        """
        self.configuration_handler = ConfigurationHandler(path=APP_CONFIG_PATH)
        configuration_data = self.configuration_handler.get_config()

        return configuration_data
