from aws_cdk import core
from multacdkrecipies import AwsApiGatewayLambdaPipes, AwsLambdaLayerVenv, AwsSsmString, AwsUserServerlessBackend

from config import CONFIG

#
# class BaseStack(core.Stack):
#     def __init__(self, scope: core.Construct, id: str, environment=None, **kwargs) -> None:
#         super().__init__(scope, id, **kwargs)
#         lambda_layer_local = AwsLambdaLayerVenv(
#             self, id="Cvm-Layer", prefix="multa_backend", environment=environment, configuration=LAMBDA_LAYER_CONFIGURATION[environment]
#         )
#         iot_policy = AwsIotPolicy(
#             self, id="Cvm-IotPolicies", prefix="multa_backend", environment=environment, configuration=IOT_POLICY[environment]
#         )
#
#
# class MultaCvmApiStack(core.Stack):
#     def __init__(self, scope: core.Construct, id: str, environment=None, **kwargs) -> None:
#         super().__init__(scope, id, **kwargs)
#         ssm_configuration = AwsSsmString(
#             self, id="Cvm-Ssm", prefix="multa_backend", environment=environment, configuration=SSM_CONFIGURATION[environment]
#         )
#         api_lambda = AwsApiGatewayLambdaPipes(
#             self, id="Cvm-Api", prefix="multa_backend", environment=environment, configuration=APIGATEWAY_CONFIGURATION[environment]
#         )
#
#         ssm_configuration.grant_read(role=api_lambda.handler_function.role)


class MultaCvmStack(core.Stack):
    """
    API Constructs to be used by MultaMetrics frontend to handle user settings, plans, roles, organizations.
    """

    def __init__(self, scope: core.Construct, id: str, config=None, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self._backend = AwsUserServerlessBackend(
            self,
            id=f"multa-cvm-backend-{config['environ']}",
            prefix=config["prefix"],
            environment=config["environ"],
            configuration=config["config"]["backend"],
        )

        self._ssm = AwsSsmString(
            self,
            id=f"multa-cvm-ssm-{config['environ']}",
            prefix=config["prefix"],
            environment=config["environ"],
            configuration=config["config"]["ssm"],
        )

        self._lambdalayer = AwsLambdaLayerVenv(
            self,
            id=f"multa-cvm-lambdalayer-{config['environ']}",
            prefix=config["prefix"],
            environment=config["environ"],
            configuration=config["config"]["lambda_layer"],
        )
        layer_arn = self._lambdalayer.lambda_layer.layer_version_arn

        for function in config["config"]["views"]["api"]["resource_trees"]:
            function["handler"]["layers"].append(layer_arn)

        self._api = AwsApiGatewayLambdaPipes(
            self,
            id=f"multa-cvm-views-{config['environ']}",
            prefix=config["prefix"],
            environment=config["environ"],
            configuration=config["config"]["views"],
        )


app = core.App()
prefix = CONFIG["prefix"]
environments = CONFIG["environments"]

for environment, configuration in environments.items():
    config = dict(prefix=prefix, environ=environment, config=configuration)
    print(config)
    MultaCvmStack(app, id=f"MultaCvmStack-{environment}", config=config)

app.synth()
