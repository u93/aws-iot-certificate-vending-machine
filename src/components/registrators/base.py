from handlers.aws import ConfigurationHandler
from settings.aws import APP_CONFIG_PATH


class BaseRegistrator:
    def __init__(self, device_request_data: dict, **kwargs):
        self.configuration_handler = None
        self.configuration_data = self.get_configuration()

        self.device_request_data = device_request_data
        self.device_registration_data = dict()
        self.valid_request_data = None
        self.valid_registration_data = None
        self.registration_result = None
        self.error = None

    def validate_request(self, **kwargs):
        raise NotImplementedError

    def transform_request(self, **kwargs):
        raise NotImplementedError

    def register(self, **kwargs):
        raise NotImplementedError

    def generate_response(self, **kwargs):
        raise NotImplementedError

    def get_configuration(self):
        self.configuration_handler = ConfigurationHandler(path=APP_CONFIG_PATH)
        configuration_data = self.configuration_handler.get_config()

        return configuration_data
