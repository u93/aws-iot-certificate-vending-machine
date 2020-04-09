import logging
import re

from handlers.aws import ThingHandlers, ConfigurationHandler


def lambda_handler(event, context):
    logging.info(event)
    logging.info("Client token: " + event["authorizationToken"])
    logging.info("Method ARN: " + event["methodArn"])
    """
    Validate the incoming token and produce the principal user 
    identifier associated with the token this could be accomplished 
    in a number of ways:
    1. Call out to OAuth provider
    2. Decode a JWT token inline
    3. Lookup in a self-managed DB
    """
    principal_id = "user|a1b2c3d4"

    """
    You can send a 401 Unauthorized response to the client by failing like so:
    raise Exception('Unauthorized')
    
    If the token is valid, a policy must be generated which will allow or deny access to the client,
    if access is denied, the client will receive a 403 Access Denied response,
    if access is allowed, API Gateway will proceed with the backend integration configured 
    on the method that was called
    this function must generate a policy that is associated with the recognized principal user identifier.
    Depending on your use case, you might store policies in a DB, or generate them on the fly 
    keep in mind, the policy is cached for 5 minutes by default (TTL is configurable in the authorizer)
    and will apply to subsequent calls to any method/resource in the RestApi made with the same token.
    """

    """
    The example policy below allows access to all resources in the RestApi
    """
    tmp = event["methodArn"].split(":")
    api_gateway_arn_tmp = tmp[5].split("/")
    aws_account_id = tmp[4]

    policy = AuthPolicy(principal_id, aws_account_id)
    policy.rest_api_id = api_gateway_arn_tmp[0]
    policy.region = tmp[3]
    policy.stage = api_gateway_arn_tmp[1]
    policy.allow_all_methods()

    """
    policy.allowMethod(HttpVerb.GET, "/pets/*")
    """

    # Finally, build the policy
    auth_response = policy.build()

    # new! -- add additional key-value pairs associated with the authenticated principal
    # these are made available by APIGW like so: $context.authorizer.<key>
    # additional context is cached
    context = {"key": "value", "number": 1, "bool": True}  # $context.authorizer.key -> value
    # context['arr'] = ['foo'] <- this is invalid, APIGW will not accept it
    # context['obj'] = {'foo':'bar'} <- also invalid

    auth_response["context"] = context

    return auth_response


class HttpVerb:
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    HEAD = "HEAD"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    ALL = "*"


class AuthPolicy(object):
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

    def __init__(self, principal, aws_account_d):
        self.aws_account_id = aws_account_d
        self.principal_id = principal
        self.allow_methods = []
        self.deny_methods = []

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
