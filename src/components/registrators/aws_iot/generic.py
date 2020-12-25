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
    def __init__(self, device_request_data):
        super(AwsIoTGenericRegistrator, self).__init__(device_request_data)

        self.thing_handler = ThingHandler()
        self.request_validation_handler = RequestAwsIoTThingSchema()
        self.registration_validation_handler = RegisterAwsIoTThingSchema()

    def validate_request(self) -> bool:
        validation_errors = self.request_validation_handler.validate(self.device_request_data)
        if validation_errors:
            self.valid_request_data = False
        else:
            self.valid_request_data = True

        return self.valid_request_data

    def transform_request(self):
        thing_name = self.device_request_data["thingName"]
        thing_type_names = self.thing_handler.get_thing_type(partial_name=thing_name)
        thing_attributes = {
            "creationDate": str(round(time.time())),
            "version": self.device_request_data["version"]
        }

        self.device_registration_data["thingName"] = thing_name
        self.device_registration_data["thingTypeName"] = thing_type_names[0] or None
        self.device_registration_data["thingAttributes"] = thing_attributes

        validation_errors = self.registration_validation_handler.validate(self.device_registration_data)
        if validation_errors:
            self.valid_request_data = False
        else:
            self.valid_request_data = True

        return self.valid_registration_data

    def get_policy(self, thing_type: str):
        policy = self.configuration_data["POLICIES"].get(thing_type)
        return policy

    def register(self):
        thing_name = self.device_registration_data["thingName"]
        thing_type = self.device_registration_data["thingTypeName"]
        thing_attributes = self.device_registration_data["thingAttributes"]

        policy = self.get_policy(thing_type=thing_type)

        logger.info("Starting thing registration in AWS IoT")
        try:
            self.thing_handler.describe_thing_(thing_name=thing_name)

        except ThingNotExists:
            logger.info("Thing does not exist, proceding to registration!")
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

            except (Exception, RuntimeError):
                logger.error("Error registering thing agent in AWS IoT")
                logger.error(traceback.format_exc())
                self.error = "Error registering thing agent in AWS IoT"
                return False

        except RuntimeError:
            logger.error("Uncaught exception... Exiting...")
            self.registration_result = False
            self.error = "Uncaught exception... Exiting..."

        else:
            logger.error("Thing exists in the AWS IoT Account, exiting...")
            self.registration_result = False
            self.error = "Thing exists in the AWS IoT Account, exiting..."

    def generate_response(self):
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

        return response
