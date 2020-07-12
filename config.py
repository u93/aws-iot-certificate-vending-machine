CONFIG = {
    "prefix": "multa-cvm",
    "environments": {
        "dev": {
            "backend": {
                "buckets": [
                    {
                        "bucket_name": "backend-static-data",
                        "versioned": True,
                        "public_read_access": False
                    }
                ],
                "dynamo_tables": [
                    {
                        "table_name": "keys",
                        "partition_key": "id",
                        "stream": {"enabled": False},
                        "billing_mode": "pay_per_request",
                    },
                ],
                "user_pool": {
                    "pool_name": "agent-managers",
                    "password_policy": {
                        "minimum_length": 8,
                        "temporary_password_duration": 1,
                        "require": {"lower_case": True, "upper_case": True, "digits": True},
                    },
                    "sign_up": {
                        "enabled": True,
                        "user_verification": {
                            "email": {
                                "subject": "Multa CVM Agent Managers Pool - Account Verification",
                                "body": "Multa CVM - Your temporary code is {####}, please use it to confirm your account.",
                                "style": "",
                            },
                            "sms": {"body": "Your temporary code is {####}, please use it to confirm your account."},
                        },
                    },
                    "invitation": {
                        "email": {
                            "subject": "Multa CVM Agent Managers Pool - Invitation",
                            "body": "Multa CVM - Your username is {username} and temporary password is {####}.",
                        },
                        "sms": {"body": "Multa CVM - Your username is {username} and temporary password is {####}."},
                    },
                    "sign_in": {"order": ["email"]},
                    "attributes": {
                        "standard": [
                            {"name": "email", "mutable": True, "required": True},
                            {"name": "given_name", "mutable": True, "required": True},
                            {"name": "family_name", "mutable": True, "required": True},
                            {"name": "phone_number", "mutable": True, "required": True},
                        ]
                    },
                    "app_client": {
                        "enabled": True,
                        "client_name": "user",
                        "generate_secret": False,
                        "auth_flows": {"custom": True, "refresh_token": True, "user_srp": True},
                    },
                },
            },
            "views": {
                "api": {
                    "apigateway_name": "api",
                    "apigateway_description": "API Gateway used for Multa Device Agents to be associated to the AWS IoT",
                    "authorizer_function": {
                        "origin": {
                            "lambda_name": "authorizer",
                            "description": "Authorizer Lambda function for Multa Device Agents",
                            "code_path": "./src",
                            "runtime": "PYTHON_3_7",
                            "handler": "authorizer.lambda_handler",
                            "layers": [],
                            "timeout": 10,
                            "environment_vars": {
                                "LOG_LEVEL": "INFO",
                                "APP_CONFIG_PATH": "/multa-cvm/dev/cvm-config-parameters"
                            },
                            "iam_actions": ["*"],
                        }
                    },
                    "settings": {
                        "proxy": False,
                        "default_cors_options": {"allow_origins": ["*"], "options_status_code": 200},
                        "default_http_methods": ["GET", "POST"],
                        "default_stage_options": {"metrics_enabled": True, "logging_level": "INFO"},
                        "default_handler": {
                            "lambda_name": "default",
                            "description": "Handler Lambda for Multa Agents Certificate Vending Machine.",
                            "code_path": "./src/",
                            "runtime": "PYTHON_3_7",
                            "handler": "default.lambda_handler",
                            "layers": [],
                            "timeout": 10,
                            "environment_vars": {
                                "LOG_LEVEL": "INFO",
                                "APP_CONFIG_PATH": "/multa_backend/dev/cvm-config-parameters",
                                "THING_TYPE_NAME_RULE": "Cvm"
                            },
                            "iam_actions": ["iot:*"],
                        },
                    },
                    "resource_trees": [
                        {
                            "resource_name": "register",
                            "methods": ["POST"],
                            "handler": {
                                "lambda_name": "register",
                                "description": "Handler Lambda for Multa Agents Certificate Vending Machine.",
                                "code_path": "./src/",
                                "runtime": "PYTHON_3_7",
                                "handler": "register.lambda_handler",
                                "layers": [],
                                "timeout": 10,
                                "environment_vars": {
                                    "LOG_LEVEL": "INFO",
                                    "APP_CONFIG_PATH": "/multa_backend/dev/cvm-config-parameters",
                                    "THING_TYPE_NAME_RULE": "Cvm"
                                },
                                "iam_actions": ["iot:*"],
                            },
                        },
                        {
                            "resource_name": "keys",
                            "methods": ["GET", "POST", "DELETE"],
                            "handler": {
                                "lambda_name": "keys",
                                "description": "Handler Lambda for Multa Agents Certificate Vending Machine.",
                                "code_path": "./src/",
                                "runtime": "PYTHON_3_7",
                                "handler": "keys.lambda_handler",
                                "layers": [],
                                "timeout": 10,
                                "environment_vars": {
                                    "LOG_LEVEL": "INFO",
                                    "APP_CONFIG_PATH": "/multa_backend/dev/cvm-config-parameters",
                                    "THING_TYPE_NAME_RULE": "Cvm"
                                },
                                "iam_actions": ["iot:*", "dynamodb:*"],
                            },
                        },
                        {
                            "resource_name": "agents",
                            "methods": ["GET", "POST", "DELETE"],
                            "handler": {
                                "lambda_name": "agents",
                                "description": "Handler Lambda for Multa Agents Certificate Vending Machine.",
                                "code_path": "./src/",
                                "runtime": "PYTHON_3_7",
                                "handler": "agents.lambda_handler",
                                "layers": [],
                                "timeout": 10,
                                "environment_vars": {
                                    "LOG_LEVEL": "INFO",
                                    "APP_CONFIG_PATH": "/multa_backend/dev/cvm-config-parameters",
                                    "THING_TYPE_NAME_RULE": "Cvm"
                                },
                                "iam_actions": ["iot:*"],
                            },
                        }
                    ]
                },
            },
            "ssm": {
                "name": "config-parameters",
                "description": "Parameters used by Multa CVM API and other applications",
                "string_value": {
                    "AWS_ROOT_CA": {
                        "PREFERRED": "https://www.amazontrust.com/repository/AmazonRootCA1.pem",
                        "BACKUP": "https://www.amazontrust.com/repository/AmazonRootCA3.pem"
                    },
                },
            },
            "lambda_layer": {
                "identifier": "cvm-layer",
                "layer_name": "layer",
                "description": "Lambda Layer containing local Python's Virtual Environment needed for Multa Lambdas.",
                "layer_runtimes": ["PYTHON_3_7"],
            }
        },
        # "demo": {
        #     "api": {},
        #     "lambda_layer": {},
        #     "ssm": {}
        # },
        # "prod": {
        #     "api": {},
        #     "lambda_layer": {},
        #     "ssm": {}
        # }
    }
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