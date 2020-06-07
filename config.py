APIGATEWAY_CONFIGURATION = {
    "dev": {
        "api": {
            "apigateway_name": "cvm-api",
            "apigateway_description": "API Gateway used for Multa Device Agents to be associated to the AWS IoT",
            "authorizer_function": {
                "origin": {
                    "lambda_name": "device_authorizer",
                    "description": "Authorizer Lambda function for Multa Device Agents",
                    "code_path": "./src",
                    "runtime": "PYTHON_3_7",
                    "handler": "authorizer.lambda_handler",
                    "layers": ["arn:aws:lambda:us-east-1:112646120612:layer:multa_backend_CvmVenvLayer_dev:1"],
                    "timeout": 10,
                    "environment_vars": {"LOG_LEVEL": "INFO", "APP_CONFIG_PATH": "/multa-cvm/dev/cvm-config-parameters"},
                    "iam_actions": ["*"],
                }
            },
            "settings": {
                "proxy": False,
                "custom_domain": {"domain_name": "cvm-agent.dev.multa.io", "certificate_arn": "arn:aws:acm:us-east-1:112646120612:certificate/48e19da0-71a4-417a-9247-c02ef100749c"},
                "default_cors_options": {"allow_origins": ["*"], "options_status_code": 200},
                "default_http_methods": ["GET", "POST"],
                "default_stage_options": {"metrics_enabled": True, "logging_level": "INFO"},
                "default_handler": {
                    "lambda_name": "device_default_handler",
                    "description": "Handler Lambda for Multa Agents Certificate Vending Machine.",
                    "code_path": "./src/",
                    "runtime": "PYTHON_3_7",
                    "handler": "handler.lambda_handler",
                    "layers": ["arn:aws:lambda:us-east-1:112646120612:layer:multa_backend_CvmVenvLayer_dev:1"],
                    "timeout": 10,
                    "environment_vars": {
                        "LOG_LEVEL": "INFO",
                        "APP_CONFIG_PATH": "/multa_backend/dev/cvm-config-parameters",
                        "THING_TYPE_NAME_RULE": "Cvm"
                    },
                    "iam_actions": ["*"],
                },
            },
            "resource_trees": [
                {
                    "resource_name": "multa-agent",
                    "methods": ["POST"],
                    "handler": {
                        "lambda_name": "device_handler",
                        "description": "Handler Lambda for Multa Agents Certificate Vending Machine.",
                        "code_path": "./src/",
                        "runtime": "PYTHON_3_7",
                        "handler": "handler.lambda_handler",
                        "layers": ["arn:aws:lambda:us-east-1:112646120612:layer:multa_backend_CvmVenvLayer_dev:1"],
                        "timeout": 10,
                        "environment_vars": {
                            "LOG_LEVEL": "INFO",
                            "APP_CONFIG_PATH": "/multa_backend/dev/cvm-config-parameters",
                            "THING_TYPE_NAME_RULE": "Cvm"
                        },
                        "iam_actions": ["*"],
                    },
                }
            ]
        }
    },
    # "demo": {},
    # "prod": {}
}

IOT_POLICY = {
    "dev": {
        "name": "multaCvmPermissionsV01",
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
                        "arn:aws:iot:us-east-1:112646120612:topic/tlm/*/${iot:Connection.Thing.ThingName}/d2c",
                        "arn:aws:iot:us-east-1:112646120612:topic/cmd/*/${iot:Connection.Thing.ThingName}/d2c",
                        "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/shadow/get",
                        "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/shadow/update",
                        # "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/jobs/start-next",
                        # "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/jobs/*/update",
                        "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/defender/metrics/*",
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": ["iot:Subscribe"],
                    "Resource": [
                        "arn:aws:iot:us-east-1:112646120612:topicfilter/cmd/*/${iot:Connection.Thing.ThingName}/c2d",
                        "arn:aws:iot:us-east-1:112646120612:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/shadow/update/*",
                        "arn:aws:iot:us-east-1:112646120612:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/shadow/get/*",
                        # "arn:aws:iot:us-east-1:112646120612:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/jobs/notify-next",
                        # "arn:aws:iot:us-east-1:112646120612:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/jobs/start-next/accepted",
                        # "arn:aws:iot:us-east-1:112646120612:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/jobs/start-next/rejected",
                        # "arn:aws:iot:us-east-1:112646120612:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/jobs/*/update/accepted",
                        # "arn:aws:iot:us-east-1:112646120612:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/jobs/*/update/rejected",
                        "arn:aws:iot:us-east-1:112646120612:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/defender/metrics/*/accepted",
                        "arn:aws:iot:us-east-1:112646120612:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/defender/metrics/*/rejected",
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": ["iot:Receive"],
                    "Resource": [
                        "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/shadow/update/*",
                        "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/shadow/get/*",
                        # "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/jobs/notify-next",
                        # "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/jobs/start-next/accepted",
                        # "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/jobs/start-next/rejected",
                        # "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/jobs/*/update/accepted",
                        # "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/jobs/*/update/rejected",
                        "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/defender/metrics/*/accepted",
                        "arn:aws:iot:us-east-1:112646120612:topic/$aws/things/${iot:Connection.Thing.ThingName}/defender/metrics/*/rejected",
                    ]
                }
            ]
        }
    },
    # "demo": {},
    # "prod": {}
}

LAMBDA_LAYER_CONFIGURATION = {
    "dev": {
        "identifier": "CvmVenvLayer",
        "layer_name": "CvmVenvLayer",
        "description": "Lambda Layer containing local Python's Virtual Environment needed for Multa CVM Auth and Handler",
        "layer_runtimes": ["PYTHON_3_7"],
    },
    # "demo": {},
    # "prod": {}
}

SSM_CONFIGURATION = {
    "dev": {
        "name": "cvm-config-parameters",
        "description": "Parameters used by Multa CVM API and other applications",
        "string_value": {
            "POLICY_NAMES": "multa_backend_multaCvmPermissionsV01_dev",
            "AWS_ROOT_CA": {
                "PREFERRED": "https://www.amazontrust.com/repository/AmazonRootCA1.pem",
                "BACKUP": "https://www.amazontrust.com/repository/AmazonRootCA3.pem"
            },
            "DEVICE_KEY": "TEST1234#",
        },
    },
    # "demo": {},
    # "prod": {}
}