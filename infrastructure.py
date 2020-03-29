from aws_cdk import core
from multacdkrecipies import AwsApiGatewayLambdaSWS, AwsLambdaLayerVenv, AwsSsmString


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
                "environment_vars": {"LOG_LEVEL": "INFO"},
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
                    "description": "Handler Lambda for Multa Agents",
                    "code_path": "./src",
                    "runtime": "PYTHON_3_7",
                    "handler": "handler.lambda_handler",
                    "timeout": 10,
                    "environment_vars": {"LOG_LEVEL": "INFO"},
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

LAMBDA_LAYER_CONFIGURATION = {
    "layer_name": "VenvLayer",
    "description": "Lambda Layer containing local Python's Virtual Environment",
    "layer_runtimes": ["PYTHON_3_7"],
}

SSM_CONFIGURATION = {
    "name": "cvm-parameters",
    "description": "Parameters used by Multa CVM API and other applications",
    "string_value": {
        "POLICY_NAMES": "multaCvmFullPermissions",
        "AWS_ROOT_CA": {"PREFERRED": "", "BACKUP": ""},
        "DEVICE_KEY": "TEST1234#",
    },
}


class LambdaLayersStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        lambda_layer_local = AwsLambdaLayerVenv(
            self, id="Layer-Venv", prefix="multa-layer", environment="dev", configuration=LAMBDA_LAYER_CONFIGURATION
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
LambdaLayersStack(app, "LambdaLayersStack-dev")
ApiStack(app, "MultaCvmApiStack-dev")

app.synth()
