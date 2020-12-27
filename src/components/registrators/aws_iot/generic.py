import time
import traceback

from components.registrators.base import BaseRegistrator
from handlers.aws import ThingHandler
from handlers.exceptions import ThingNotExists
from handlers.utils import Logger
from handlers.validations import RegisterAwsIoTThingSchema, RequestAwsIoTThingSchema


project_logger = Logger()
logger = project_logger.get_logger()


class AwsIoTGenericRegistrator(BaseRegistrator):
    class Meta:
        WORKERS = {
            "request_validation_handler": RequestAwsIoTThingSchema,
            "registration_validation_handler": RegisterAwsIoTThingSchema,
            "thing_handler": ThingHandler
        }

    def __init__(self, device_request_data):
        super(AwsIoTGenericRegistrator, self).__init__(device_request_data)

        self.request_validation_handler = self.Meta.WORKERS["request_validation_handler"]()
        self.registration_validation_handler = self.Meta.WORKERS["registration_validation_handler"]()
        self.thing_handler = self.Meta.WORKERS["thing_handler"]()

    def validate_request(self) -> bool:
        """
        Validates the HTTP request sent by the agent that will be registered.
        :return: Boolean with result of the request validation process.
        """
        validation_errors = self.request_validation_handler.validate(self.device_request_data)
        if validation_errors:
            self.valid_request_data = False
        else:
            self.valid_request_data = True

        return self.valid_request_data

    def transform_request(self):
        """
        Enriches the request that the agent sent with custom parameters and validates the enrichment.
        :return: Boolean with result of the registration data validation process.
        """
        thing_attributes = {
            "creationDate": str(round(time.time())),
            "version": self.device_request_data["version"]
        }

        self.device_registration_data["thingName"] = self.device_request_data["thingName"]
        self.device_registration_data["thingTypeName"] = self.get_thing_type()
        self.device_registration_data["thingAttributes"] = thing_attributes

        validation_errors = self.registration_validation_handler.validate(self.device_registration_data)
        if validation_errors:
            self.valid_registration_data = False
        else:
            self.valid_registration_data = True

        return self.valid_registration_data

    def register(self) -> bool:
        """
        Registers the agent into AWS IoT. Validation ocurrs in case that the AWS IoT Thing already exists by name.
        Steps are, the AWS IoT Policy is obtained based on the AWS IoT Thing Type, the Thing Attributes are generated
        and validated based on the AWS IoT Thing Type. Finally the registration is executing using the Boto3 proper steps.
        :return:
        """
        thing_name = self.device_registration_data["thingName"]
        thing_type = self.device_registration_data["thingTypeName"]

        raw_thing_attributes = self.device_registration_data["thingAttributes"]
        thing_attributes = self.generate_attributes(
            thing_type=thing_type, validated_attributes=raw_thing_attributes
        )

        policy = self.get_policy(thing_type=thing_type)

        logger.info("Starting thing registration in AWS IoT")
        try:
            self.thing_handler.describe_thing_(thing_name=thing_name)

        except ThingNotExists:
            logger.info("Thing does not exist, preceding to registration!")
            try:
                self.thing_handler.get_preconfigured_policy(policy_name=policy)
                certificate_data, certificate_arn = self.thing_handler.provision_thing()
                self.thing_handler.attach_policy_(policy_name=policy, certificate_arn=certificate_arn)
                self.thing_handler.create_thing_(
                    thing_name=thing_name,
                    thing_type=thing_type,
                    thing_attributes=thing_attributes,
                )
                self.thing_handler.attach_thing_principal_(thing_name=thing_name, certificate_arn=certificate_arn)
                root_ca = self.thing_handler.get_root_ca(
                    preferred_endpoint=self.configuration_data["AWS_ROOT_CA"]["PREFERRED"],
                    backup_endpoint=self.configuration_data["AWS_ROOT_CA"]["BACKUP"],
                )

                self.registration_result = dict(certificate_data=certificate_data, root_ca=root_ca)
                self.code = 200

                return True

            except (Exception, RuntimeError):
                logger.error("Error registering thing agent in AWS IoT")
                logger.error(traceback.format_exc())
                self.error = "Error registering thing agent in AWS IoT"
                self.code = 400

                return False

        except RuntimeError:
            logger.error("Uncaught exception... Exiting...")
            self.registration_result = False
            self.error = "Uncaught exception... Exiting..."
            self.code = 500

            return False

        else:
            logger.error("Thing exists in the AWS IoT Account, exiting...")
            self.registration_result = False
            self.error = "Thing exists in the AWS IoT Account, exiting..."
            self.code = 400

            return False

    def get_thing_type(self):
        prefix = "Cvm"
        thing_type_names = self.thing_handler.get_thing_type(partial_name=prefix)

        return self.select_thing_type(thing_types=thing_type_names)

    @staticmethod
    def select_thing_type(thing_types: list):
        return thing_types[0] or None

    def generate_attributes(self, thing_type: str, validated_attributes: dict) -> dict:
        defined_attributes = self.get_defined_attributes(thing_type=thing_type)
        attributes = dict()
        for attribute, value in validated_attributes.items():
            if attribute in defined_attributes:
                attributes[attribute] = value

        return attributes

    def get_defined_attributes(self, thing_type: str) -> list:
        raw_attributes = self.configuration_data["ATTRIBUTES"].get(thing_type)
        defined_attributes = [attribute["name"] for attribute in raw_attributes]

        return defined_attributes

    def get_policy(self, thing_type: str) -> str:
        policy = self.configuration_data["POLICIES"].get(thing_type, {}).get("name")
        return policy
