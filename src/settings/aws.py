import boto3


class CvmConfiguration:
    def __init__(self):
        # TODO: ADD SSM PARAMETER STORE CLIENT
        pass

    @staticmethod
    def get_default_policy():
        return get_config_file()["cvm"]["default_policy"]

    @staticmethod
    def get_secret_key():
        return get_config_file()["cvm"]["secret_key"]

    @staticmethod
    def get_root_ca_endpoint(type: str):
        return get_config_file()["cvm"]["iotRootCAEndpoint"][type]

    @staticmethod
    def get_defined_thing_types():
        types_names = []
        types = get_config_file()["account"]["thing_types"]
        for element in types:
            types_names.append(element["name"])

        return types_names
