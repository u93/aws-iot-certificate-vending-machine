from aws_cdk import core
from multacdkrecipies import AwsApiGatewayLambdaPipes, AwsLambdaLayerVenv, AwsSsmString, AwsUserServerlessBackend


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
prefix = app.node.try_get_context("prefix")
environments = app.node.try_get_context("environments")

for environment, configuration in environments.items():
    if configuration is None:
        continue

    id_ = f"MultaCvmStack-{environment}"
    config = dict(prefix=prefix, environ=environment, config=configuration)
    MultaCvmStack(app, id=id_, config=config)

app.synth()
