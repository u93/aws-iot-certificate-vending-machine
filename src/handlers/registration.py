import traceback

from .aws import ThingHandlers
from .exceptions import ThingNotExists
from settings.aws import CvmConfiguration
from .utils import Logger


project_logger = Logger()
logger = project_logger.get_logger()


class CvmRegistration:
    def __init__(self, thing_data: dict, thing_name=None, policy_name=None):
        self.thing_handler = ThingHandlers()
        self.thing_data = thing_data
        self.thing_name = thing_data["thingName"]
        if policy_name is None:
            self.policy = CvmConfiguration().get_default_policy()
        else:
            self.policy = policy_name

    def register_thing(self):
        logger.info("Starting thing registration in AWS IoT")
        try:
            thing_data = self.thing_handler.describe_thing_(thing_name=self.thing_name)
        except ThingNotExists:
            logger.info("Thing does not exist, proceding to registration!")
            try:
                policy_arn = self.thing_handler.get_preconfigured_policy(policy_name=self.policy)
                certificate_data, certificate_arn = self.thing_handler.provision_thing()
                self.thing_handler.attach_policy_(policy_name=self.policy, certificate_arn=certificate_arn)
                self.thing_handler.create_thing_(
                    thing_name=self.thing_name,
                    thing_type=self.thing_data["thing_type"],
                    thing_attributes=self.thing_data["thing_attributes"],
                )
                self.thing_handler.attach_thing_principal_(thing_name=self.thing_name, certificate_arn=certificate_arn)
                root_ca = self.thing_handler.get_root_ca()
            except (Exception, RuntimeError):
                logger.error("Error registering thing agent in AWS IoT")
                logger.error(traceback.format_exc())
                return False
            else:
                return dict(certificate_data=certificate_data, root_ca=root_ca)
        except RuntimeError:
            logger.error("Uncaught exception... Exiting...")
            return False
        else:
            logger.error("Thing exists in the AWS IoT Account, exiting...")
            return False
