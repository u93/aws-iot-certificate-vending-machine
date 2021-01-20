import json
import traceback

import boto3
from botocore.exceptions import ClientError
import re
import requests

from .exceptions import IoTBotoError, QueryError, ThingNotExists
from .utils import Logger, HttpVerb
from settings.aws import USER_POOL_ID

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


class IamAuthPolicyHandler(object):
    aws_account_id = ""
    """
    The AWS account id the policy will be generated for. This is used to create the method ARNs.
    """
    principal_id = ""
    """
    The principal used for the policy, this should be a unique identifier for the end user.
    """
    version = "2012-10-17"
    """
    The policy version used for the evaluation. This should always be '2012-10-17'
    """
    path_regex = "^[/.a-zA-Z0-9-\*]+$"
    """
    The regular expression used to validate resource paths for the policy.
    """

    """
    These are the internal lists of allowed and denied methods. These are lists
    of objects and each object has 2 properties: A resource ARN and a nullable
    conditions statement.
    The build method processes these lists and generates the approriate
    statements for the final policy.
    """
    allow_methods = []
    deny_methods = []

    rest_api_id = "*"
    """
    The API Gateway API id. By default this is set to '*'
    """

    region = "*"
    """
    The region where the API is deployed. By default this is set to '*'
    """

    stage = "*"
    """
    The name of the stage used in the policy. By default this is set to '*'
    """

    def __init__(self):
        self.aws_account_id = None
        self.principal_id = None
        self.allow_methods = []
        self.deny_methods = []

    def populate(self, aws_account_id, principal_id):
        self.aws_account_id = aws_account_id
        self.principal_id = principal_id

    def _add_method(self, effect, verb, resource, conditions):
        """Adds a method to the internal lists of allowed or denied methods. Each object in
        the internal list contains a resource ARN and a condition statement. The condition
        statement can be null."""
        if verb != "*" and not hasattr(HttpVerb, verb):
            raise NameError("Invalid HTTP verb " + verb + ". Allowed verbs in HttpVerb class")
        resource_pattern = re.compile(self.path_regex)
        if not resource_pattern.match(resource):
            raise NameError("Invalid resource path: " + resource + ". Path should match " + self.path_regex)

        if resource[:1] == "/":
            resource = resource[1:]

        resource_arn = (
            "arn:aws:execute-api:"
            + self.region
            + ":"
            + self.aws_account_id
            + ":"
            + self.rest_api_id
            + "/"
            + self.stage
            + "/"
            + verb
            + "/"
            + resource
        )

        if effect.lower() == "allow":
            self.allow_methods.append({"resourceArn": resource_arn, "conditions": conditions})
        elif effect.lower() == "deny":
            self.deny_methods.append({"resourceArn": resource_arn, "conditions": conditions})

    @staticmethod
    def _get_empty_statement(effect):
        """
        Returns an empty statement object prepopulated with the correct action and the
        desired effect.
        """
        statement = {"Action": "execute-api:Invoke", "Effect": effect[:1].upper() + effect[1:].lower(), "Resource": []}

        return statement

    def _get_statement_for_effect(self, effect, methods):
        """T
        his function loops over an array of objects containing a resourceArn and
        conditions statement and generates the array of statements for the policy.
        """
        statements = []

        if len(methods) > 0:
            statement = self._get_empty_statement(effect)

            for curMethod in methods:
                if curMethod["conditions"] is None or len(curMethod["conditions"]) == 0:
                    statement["Resource"].append(curMethod["resourceArn"])
                else:
                    conditional_statement = self._get_empty_statement(effect)
                    conditional_statement["Resource"].append(curMethod["resourceArn"])
                    conditional_statement["Condition"] = curMethod["conditions"]
                    statements.append(conditional_statement)

            statements.append(statement)

        return statements

    def allow_all_methods(self):
        """
        Adds a '*' allow to the policy to authorize access to all methods of an API
        """
        self._add_method("Allow", HttpVerb.ALL, "*", [])

    def deny_all_methods(self):
        """
        Adds a '*' allow to the policy to deny access to all methods of an API
        """
        self._add_method("Deny", HttpVerb.ALL, "*", [])

    def allow_method(self, verb, resource):
        """
        Adds an API Gateway method (Http verb + Resource path) to the list of allowed
        methods for the policy
        """
        self._add_method("Allow", verb, resource, [])

    def deny_method(self, verb, resource):
        """
        Adds an API Gateway method (Http verb + Resource path) to the list of denied
        methods for the policy
        """
        self._add_method("Deny", verb, resource, [])

    def allow_method_with_conditions(self, verb, resource, conditions):
        """
        Adds an API Gateway method (Http verb + Resource path) to the list of allowed
        methods and includes a condition for the policy statement. More on AWS policy
        conditions here: http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html#Condition
        """
        self._add_method("Allow", verb, resource, conditions)

    def deny_method_with_conditions(self, verb, resource, conditions):
        """
        Adds an API Gateway method (Http verb + Resource path) to the list of denied
        methods and includes a condition for the policy statement. More on AWS policy
        conditions here: http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html#Condition
        """
        self._add_method("Deny", verb, resource, conditions)

    def build(self):
        """Generates the policy document based on the internal lists of allowed and denied
        conditions. This will generate a policy with two main statements for the effect:
        one statement for Allow and one statement for Deny.
        Methods that includes conditions will have their own statement in the policy."""
        if (self.allow_methods is None or len(self.allow_methods) == 0) and (
            self.deny_methods is None or len(self.deny_methods) == 0
        ):
            raise NameError("No statements defined for the policy")

        policy = {"principalId": self.principal_id, "policyDocument": {"Version": self.version, "Statement": []}}

        policy["policyDocument"]["Statement"].extend(self._get_statement_for_effect("Allow", self.allow_methods))
        policy["policyDocument"]["Statement"].extend(self._get_statement_for_effect("Deny", self.deny_methods))

        return policy


class ConfigurationHandler(Sts):
    """
    Handles the boto3 calss for SSM configuration.
    """

    def __init__(self, path: str):
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


class ThingHandler(Sts):
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
            logger.error("Boto3 error... Unable to attach policy!")
            logger.error(traceback.format_exc())
            raise IoTBotoError

        except Exception:
            logger.error("Unexpected error...")
            logger.error(traceback.format_exc())
            raise RuntimeError

    def attach_thing_principal_(self, thing_name: str, certificate_arn: str):
        logger.info("Attaching IoT thing principal...")
        try:
            response = self.iot_client.attach_thing_principal(thingName=thing_name, principal=certificate_arn)

        except ClientError:
            logger.error("Boto3 error... Unable to attach thing to its principal!")
            logger.error(traceback.format_exc())
            raise IoTBotoError

        except Exception:
            logger.error("Unexpected error...")
            logger.error(traceback.format_exc())
            raise RuntimeError

    def create_thing_(self, thing_name: str, thing_type: str, thing_attributes: dict):
        logger.info("Creating thing...")
        try:
            response = self.iot_client.create_thing(
                thingName=thing_name, thingTypeName=thing_type, attributePayload={"attributes": thing_attributes},
            )

        except ClientError:
            logger.error("Boto3 error... Unable to create thing!")
            logger.error(traceback.format_exc())
            raise IoTBotoError

        except Exception:
            logger.error("Unexpected error...")
            logger.error(traceback.format_exc())
            raise RuntimeError

    def describe_thing_(self, thing_name: str) -> dict:
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
            logger.error("Boto3 error... Probably thing does not exist!")
            raise ThingNotExists

        except Exception:
            logger.error("Unexpected error...")
            logger.error(traceback.format_exc())
            raise RuntimeError

        else:
            return thing_data

    def get_preconfigured_policy(self, policy_name: str) -> dict:
        logger.info("Getting preconfigured policy...")
        try:
            response = self.iot_client.get_policy(policyName=policy_name)["policyArn"]

        except ClientError:
            logger.error(traceback.format_exc())
            raise IoTBotoError

        except Exception:
            logger.error("Unexpected error...")
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
            return r.text
        else:
            return False

    def get_thing_types_by_prefix(self, partial_name: str):
        thing_types = list()
        response = self.iot_client.list_thing_types(maxResults=10)
        thing_types.extend(response["thingTypes"])
        next_token = response.get("nextToken")
        while next_token is not None:
            try:
                next_token = response.get("nextToken")
                if next_token is None:
                    response = self.iot_client.list_thing_types(maxResults=10)
                else:
                    response = self.iot_client.list_thing_types(maxResults=10, nextToken=next_token)

            except ClientError:
                logger.error("Boto3 error...")
                logger.error(traceback.format_exc())

            except Exception:
                logger.error("Unexpected error...")
                logger.error(traceback.format_exc())

            thing_types.extend(response["thingTypes"])

        logger.info(thing_types)
        results = [
            thing_type["thingTypeName"]
            for thing_type in thing_types
            if partial_name.lower() in thing_type["thingTypeName"].lower()
        ]

        logger.info("Returning policies...")
        return results

    def provision_thing(self, certificate_status=True):
        logger.info("Provisioning thing certificates...")
        try:
            response = self.iot_client.create_keys_and_certificate(setAsActive=certificate_status)
            certificate_data = {
                "pem": response["certificatePem"],
                "key_pair": {
                    "public_key": response["keyPair"]["PublicKey"],
                    "private_key": response["keyPair"]["PrivateKey"],
                },
            }
            certificate_arn = response["certificateArn"]

        except ClientError:
            logger.error(traceback.format_exc())
            raise IoTBotoError

        except Exception:
            logger.error("Unexpected error...")
            logger.error(traceback.format_exc())
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

        except Exception:
            logger.error("Unexpected error...")
            logger.error(traceback.format_exc())
            raise RuntimeError

        return response


class ThingPolicyHandlers(Sts):
    def __init__(self):
        Sts.__init__(self)
        self.iot_client = boto3.client("iot")

    def _get_policy(self):
        pass

    def _create_policy(self):
        pass

    def _update_policy(self):
        pass

    def _delete_policy(self):
        pass

    def generate_minimum_policy(self):
        pass

    def generate_base_policy(self):
        pass

    def generate_full_policy(self):
        pass


class CognitoHandler(Sts):
    def __init__(self):
        Sts.__init__(self)
        self.cognito_client = boto3.client("cognito-idp")

    def check_user(self, email_address: str):
        response = self.cognito_client.list_users(
            UserPoolId=USER_POOL_ID, AttributesToGet=[], Limit=10, Filter=f"email = '{email_address}'"
        )
        if len(response["Users"]) == 1:
            return response["Users"]
        else:
            return False

    def get_user(self, user_id: str):
        user_response = dict(user_id=None, user_attributes=None)
        try:
            response = self.cognito_client.admin_get_user(UserPoolId=USER_POOL_ID, Username=user_id)
        except Exception:
            logger.error("Error getting user by ID")
            logger.error(traceback.format_exc())
            return False
        else:
            user_response["user_id"] = response["Username"]
            user_response["user_attributes"] = response["UserAttributes"]
            return user_response

    def get_user_by_access_token(self, access_token: str):
        user_response = dict(user_id=None, user_attributes=None)
        try:
            response = self.cognito_client.get_user(AccessToken=access_token)
        except Exception:
            logger.error("Error GETTING USER by ACCESS Token")
            logger.error(traceback.format_exc())
            return False
        else:
            user_response["user_id"] = response["Username"]
            user_response["user_attributes"] = response["UserAttributes"]
            return user_response

    def list_users(self, pagination_token=None):
        kwargs = {
            "UserPoolId": USER_POOL_ID,
            "Limit": 20,
        }
        if pagination_token is not None:
            kwargs["PaginationToken"] = pagination_token
        response = self.cognito_client.list_users(**kwargs)
        return response
