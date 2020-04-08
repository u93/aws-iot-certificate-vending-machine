import json
import traceback

import boto3
from botocore.exceptions import ClientError
import requests

from .exceptions import IoTBotoError, QueryError, ThingNotExists
from .utils import Logger

project_logger = Logger()
logger = project_logger.get_logger()


class Session:
    def __init__(self):
        self._user_session = boto3.session.Session()
        self.user_region = self._user_session.region_name


class Sts(Session):
    def __init__(self):
        Session.__init__(self)
        self._account_client = boto3.client("sts")
        self.account_id = self._account_client.get_caller_identity()["Account"]


class ConfigurationHandler(Sts):
    """
    Handles the boto3 calss for SSM configuration.
    """

    def __init__(self, path):
        Sts.__init__(self)
        self.ssm_client = boto3.client("ssm")
        self.path = path
        self.configuration = None

    def get_config(self):
        try:
            parameter_details = self.ssm_client.get_parameters_by_path(Path=self.path, Recursive=False)
            logger.info(parameter_details)
            if "Parameters" in parameter_details and len(parameter_details.get("Parameters")) > 0:
                for param in parameter_details.get("Parameters"):
                    config_values = json.loads(param.get("Value"))
                    self.configuration = config_values
        except Exception:
            logger.error("Encountered an error loading config from SSM.")
            logger.error(traceback.print_exc())
        finally:
            logger.info(self.configuration)
            return self.configuration


class ThingHandlers(Sts):
    """
    Handles the boto3 calls for thing management. Includes Things, Thing Types, Policies, Certificates and Thing
    Indexing.
    """

    def __init__(self):
        Sts.__init__(self)
        self.iot_client = boto3.client("iot")

    def attach_policy_(self, policy_name: str, certificate_arn: str):
        logger.info("Attaching IoT policy...")
        try:
            response = self.iot_client.attach_policy(policyName=policy_name, target=certificate_arn)
        except ClientError:
            logger.error(traceback.format_exc())
            raise IoTBotoError

    def attach_thing_principal_(self, thing_name: str, certificate_arn: str):
        logger.info("Attaching IoT thing principal...")
        try:
            response = self.iot_client.attach_thing_principal(thingName=thing_name, principal=certificate_arn)
        except ClientError:
            logger.error(traceback.format_exc())
            raise IoTBotoError

    def create_thing_(self, thing_name: str, thing_type: str, thing_attributes: dict):
        logger.info("Creating thing...")
        try:
            # self.thing_type = kwargs.get("thingTypeName", None)
            # self.thing_attributes = kwargs.get("attributePayload", None)
            response = self.iot_client.create_thing(
                thingName=thing_name, thingTypeName=thing_type, attributePayload=thing_attributes,
            )
        except ClientError:
            logger.error(traceback.format_exc())
            raise IoTBotoError

    def describe_thing_(self, thing_name):
        logger.info("Describing thing...")
        try:
            response = self.iot_client.describe_thing(thingName=thing_name)
            thing_data = {
                "thing_arn": response["thingArn"],
                "thing_name": response["thingName"],
                "thing_type_name": response["thingTypeName"],
                "attributes": response["attributes"],
                "version": response["version"],
            }
        except ClientError:
            raise ThingNotExists
        except Exception:
            raise RuntimeError
        else:
            return thing_data

    def get_preconfigured_policy(self, policy_name: str):
        logger.info("Getting preconfigured policy...")
        try:
            response = self.iot_client.get_policy(policyName=policy_name)["policyArn"]
        except ClientError:
            logger.error(traceback.format_exc())
            raise RuntimeError
        else:
            return response

    @staticmethod
    def get_root_ca(preferred_endpoint: str, backup_endpoint: str):
        try:
            r = requests.get(url=preferred_endpoint)
            r.raise_for_status()
        except Exception:
            logger.error("Using backup certficate endpoint...")
            logger.error(traceback.format_exc())
            r = requests.get(url=backup_endpoint)

        if r.status_code == 200:
            logger.info(r.text)
            return r.text
        else:
            return False

    def get_thing_type(self, partial_name: str):
        thing_types = list()
        response = self.iot_client.list_thing_types(maxResults=1)
        next_token = response.get("nextToken")
        while next_token is not None:
            try:
                next_token = response.get("nextToken")
                print(next_token)
                if next_token is None:
                    response = self.iot_client.list_thing_types(maxResults=1)
                else:
                    response = self.iot_client.list_thing_types(maxResults=1, nextToken=next_token)
            except Exception as e:
                logger.error(e)
                raise RuntimeError
            thing_types.extend(response["thingTypes"])

        results = [
            thing_type["thingTypeName"] for thing_type in thing_types if partial_name in thing_type["thingTypeName"].lower()
        ]

        return results[0]

    def provision_thing(self, certificate_status=True):
        logger.info("Provisioning thing certificates...")
        try:
            response = self.iot_client.create_keys_and_certificate(setAsActive=certificate_status)
            certificate_data = {
                "pem": response["certificatePem"],
                "key_pair": {"public_key": response["keyPair"]["PublicKey"], "private_key": response["keyPair"]["PrivateKey"],},
            }
            certificate_arn = response["certificateArn"]
        except ClientError:
            logger.error(traceback.format_exc())
            raise IoTBotoError
        except Exception:
            raise RuntimeError
        else:
            return certificate_data, certificate_arn

    def search_things(self, query: str):
        logger.info(f"Searching things with query: {query}")
        try:
            response = self.iot_client.search_index(queryString=query)["things"]
        except ClientError:
            logger.error(traceback.format_exc())
            raise QueryError(f"Issue with query: {query}")
        return response
