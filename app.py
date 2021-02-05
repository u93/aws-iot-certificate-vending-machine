from aws_cdk import core
from multacdkrecipies import AwsApiGatewayLambdaPipes, AwsLambdaLayerVenv, AwsSsmString, AwsIotAnalyticsSimplePipeline


class MultaCvmStack(core.Stack):
    """
    API Constructs to be used by MultaMetrics frontend to handle user settings, plans, roles, organizations.
    """

    def __init__(self, scope: core.Construct, id: str, config=None, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

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

        config["config"]["views"]["api"]["authorizer_function"]["origin"]["layers"].append(layer_arn)
        for function in config["config"]["views"]["api"]["resource_trees"]:
            function["handler"]["layers"].append(layer_arn)

        self._api = AwsApiGatewayLambdaPipes(
            self,
            id=f"multa-cvm-views-{config['environ']}",
            prefix=config["prefix"],
            environment=config["environ"],
            configuration=config["config"]["views"],
        )

        self._iot_registry_cold_pipeline = AwsIotAnalyticsSimplePipeline(
            self,
            id=f"multa-cvm-iotpipeline-cold-{config['environ']}",
            prefix=config["prefix"],
            environment=config["environ"],
            configuration=config["config"]["iot_registry_cold_events_pipeline"],
        )


app = core.App()
prefix = app.node.try_get_context("prefix")
environments = app.node.try_get_context("environments")

for environment, configuration in environments.items():
    if configuration is None:
        continue

    id_ = f"MultaCvmStack-{environment}"
    config = dict(prefix=prefix, environ=environment, config=configuration)
    MultaCvmStack(app, id=id_, config=config)

app.synth()
