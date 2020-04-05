from aws_cdk import core
from multacdkrecipies import AwsApiGatewayLambdaSWS, AwsIotPolicy, AwsLambdaLayerVenv, AwsSsmString


APIGATEWAY_CONFIGURATION = {
    "api": {
        "apigateway_name": "cvm-api",
        "apigateway_description": "API Gateway used for devices to be added to the AWS IoT",
        "proxy": False,
        "lambda_authorizer": {
            "origin": {
                "lambda_name": "authorizer",
                "description": "Handler Lambda for Multa Agents",
                "code_path": "./src",
                "runtime": "PYTHON_3_7",
                "handler": "authorizer.lambda_handler",
                "timeout": 10,
                "environment_vars": {"LOG_LEVEL": "INFO", "APP_CONFIG_PATH": "/multa-cvm/dev/cvm-config-parameters"},
                "iam_actions": ["*"],
            },
            "alarms": [
                {"name": "metric_errors", "number": 2, "periods": 2, "points": 1, "actions": True,},
                {"name": "metric_invocations", "number": 2, "periods": 2, "points": 1, "actions": True,},
            ],
        },
        "resource": {
            "name": "multa-agent",
            "allowed_origins": ["*"],
            "methods": ["GET", "POST", "DELETE"],
            "custom_domain": {
                "domain_name": "cvm-agent.dev.multa.io",
                "certificate_arn": "arn:aws:acm:us-east-1:112646120612:certificate/48e19da0-71a4-417a-9247-c02ef100749c",
            },
            "handler": {
                "origin": {
                    "lambda_name": "handler",
                    "description": "Handler Lambda for Multa Agents Certificate Vending Machine",
                    "code_path": "./src",
                    "runtime": "PYTHON_3_7",
                    "layers": ["arn:aws:lambda:us-east-1:112646120612:layer:multa-base_VenvLayer_dev:1"],
                    "handler": "handler.lambda_handler",
                    "timeout": 10,
                    "environment_vars": {"LOG_LEVEL": "INFO", "APP_CONFIG_PATH": "/multa-cvm/dev/cvm-config-parameters"},
                    "iam_actions": ["*"],
                },
                "alarms": [
                    {"name": "metric_errors", "number": 2, "periods": 2, "points": 1, "actions": True,},
                    {"name": "metric_invocations", "number": 2, "periods": 2, "points": 1, "actions": True,},
                ],
            },
        },
    }
}

IOT_POLICY = {
    "name": "multaCvmPermissions",
    "policy_document": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["iot:Connect"],
                "Resource": ["arn:aws:iot:us-east-1:112646120612:client/${iot:Connection.Thing.ThingName}"]
            },
            {
                "Effect": "Allow",
                "Action": ["iot:Publish"],
                "Resource": [
                    "arn:aws:iot:us-east-1:112646120612:topic/tlm/system/${iot:Connection.Thing.ThingName}/d2c",
                    "arn:aws:iot:us-east-1:112646120612:topic/tlm/processes/${iot:Connection.Thing.ThingName}/d2c",
                    "arn:aws:iot:us-east-1:112646120612:topic/cmd/actions/${iot:Connection.Thing.ThingName}/d2c",
                    "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/shadow/update",
                    "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/shadow/get"
                ]
            },
            {
                "Effect": "Allow",
                "Action": ["iot:Subscribe"],
                "Resource": [
                    "arn:aws:iot:us-east-1:112646120612:topicfilter/cmd/actions/${iot:Connection.Thing.ThingName}/c2d",
                    "arn:aws:iot:us-east-1:112646120612:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/shadow/update/documents",
                    "arn:aws:iot:us-east-1:112646120612:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/shadow/update/delta",
                    "arn:aws:iot:us-east-1:112646120612:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/shadow/get/accepted"
                ]
            },
            {
                "Effect": "Allow",
                "Action": ["iot:Receive"],
                "Resource": [
                    "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/shadow/update/accepted",
                    "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/shadow/update/delta",
                    "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/shadow/get"
                ]
            }
        ]
    }
}

LAMBDA_LAYER_CONFIGURATION = {
    "layer_name": "VenvLayer",
    "description": "Lambda Layer containing local Python's Virtual Environment",
    "layer_runtimes": ["PYTHON_3_7"],
}

SSM_CONFIGURATION = {
    "name": "cvm-config-parameters",
    "description": "Parameters used by Multa CVM API and other applications",
    "string_value": {
        "POLICY_NAMES": "multa-base_multaCvmPermissions_dev",
        "AWS_ROOT_CA": {
            "PREFERRED": "https://www.amazontrust.com/repository/AmazonRootCA1.pem",
            "BACKUP": "https://www.amazontrust.com/repository/AmazonRootCA3.pem"
        },
        "DEVICE_KEY": "TEST1234#",
    },
}


class BaseStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        lambda_layer_local = AwsLambdaLayerVenv(
            self, id="Layer-Venv", prefix="multa-base", environment="dev", configuration=LAMBDA_LAYER_CONFIGURATION
        )
        iot_policy = AwsIotPolicy(
            self, id="Iot-Policies", prefix="multa-base", environment="dev", configuration=IOT_POLICY
        )


class ApiStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        ssm_configuration = AwsSsmString(
            self, id="Api-Ssm", prefix="multa-cvm", environment="dev", configuration=SSM_CONFIGURATION
        )
        api_lambda = AwsApiGatewayLambdaSWS(
            self, id="Api-Sws", prefix="multa-cvm", environment="dev", configuration=APIGATEWAY_CONFIGURATION
        )

        ssm_configuration.grant_read(role=api_lambda.lambda_handler_function.role)


app = core.App()
BaseStack(app, "BaseStack-dev")
ApiStack(app, "MultaCvmApiStack-dev")

app.synth()
