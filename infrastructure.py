from aws_cdk import core
from multacdkrecipies import AwsApiGatewayLambdaPipes, AwsIotPolicy, AwsLambdaLayerVenv, AwsSsmString

from config import APIGATEWAY_CONFIGURATION, IOT_POLICY, LAMBDA_LAYER_CONFIGURATION, SSM_CONFIGURATION


class BaseStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, environment=None, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        lambda_layer_local = AwsLambdaLayerVenv(
            self, id="Cvm-Layer", prefix="multa_backend", environment=environment, configuration=LAMBDA_LAYER_CONFIGURATION[environment]
        )
        iot_policy = AwsIotPolicy(
            self, id="Cvm-IotPolicies", prefix="multa_backend", environment=environment, configuration=IOT_POLICY[environment]
        )


class MultaCvmApiStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, environment=None, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        ssm_configuration = AwsSsmString(
            self, id="Cvm-Ssm", prefix="multa_backend", environment=environment, configuration=SSM_CONFIGURATION[environment]
        )
        api_lambda = AwsApiGatewayLambdaPipes(
            self, id="Cvm-Api", prefix="multa_backend", environment=environment, configuration=APIGATEWAY_CONFIGURATION[environment]
        )

        ssm_configuration.grant_read(role=api_lambda.handler_function.role)


app = core.App()
environments = ["dev"]

for environment in environments:
    BaseStack(app, f"BaseStack-{environment}", environment=environment)
    MultaCvmApiStack(app, f"MultaCvmApiStack-{environment}", environment=environment)

app.synth()
