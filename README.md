# AWS IoT Device Registration Gateway


- Designed to provide a common registration entrypoint for AWS IoT devices.
- Avoids complexity of current AWS IoT fleet provisioning workflows.
    - Not integrated into Cloudformation or other cloud deployment frameworks.
    - Certificates required to be provisioned into devices.
    - Requires advanced AWS IoT knowledge.
- Easy to deploy / maintain / keep source control with AWS CDK and Cloudformation.
- Code architecture designed to be easily extendable to cover custom cases.
- Designed for Serverless Architecture, portable to other types of architectures.

**Architecture**
---
![cmv-architecture](etc/architecture/aws-iot-cvm-regular-architecture-transparent.png)


**Installation**
---

1. Install AWS CDK (Getting started guide can be followed [`here`](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html))
    + `$ npm install -g aws-cdk`
    
2. Install Python dependencies (make sure to use Python3.7 or newer)
    + `pip install -r etc/pip/requirements.txt`
    
3. Make sure that you have Docker installed and running, will be required to build Python's dependencies


**Usage**
---

1. Add modification to `cdk.json` in order to add customizations to your project.

2. Modify `cdk.json` and add your desired tokens in `ssm.string_value.DEVICE_AUTHORIZER_VALID_TOKENS`.

3. Add your desired AWS IoT Thing types in the AWS console, copy the name and use it in:
    - `ssm.string_value.DEVICE_AUTHORIZER_VALID_TOKENS.POLICIES.${THING_TYPE}.name`
    - `ssm.string_value.ATTRIBUTES.$TYPE.[].name`

4. Add the AWS IoT Thing Policy and add name to `ssm.string_value.DEVICE_AUTHORIZER_VALID_TOKENS.POLICIES.${THING_TYPE}.name` .

5. Execute `cdk diff` and `cdk deploy` to deploy your project.

6. Default environment created is `dev` but other environments can be created by adding keys to `cdk.json` at the same level that `dev` is.


**Structure**
---

- API Gateway that points to a Lambda function.
- Lambda Function that will be in charge of authorize and register devices plus will return the certificate information to the registering devices.
    - Lambda Layer with external dependencies.
- SSM Parameter Store that will contain the application configuration.
- AWS IoT Analytics data storage for AWS IoT Registry events (broker subscription has to be enabled in AWS IoT).


**Default API Endpoints and Registration payload**
---

- API Endpoint:
    - `${API_GATEWAY_STAGE_URL}/register`
- Method:
    - `POST`
- Headers:
    - `Authorization: ${TOKEN DEVICE_AUTHORIZER_TOKEN_IDENTIFIER} ${DEVICE_TOKEN}`
    - `${DEVICE_AUTHORIZER_TOKEN_IDENTIFIER}` -> Defined AWS SSM Parameter Store
    - `DEVICE_TOKEN` should be one of the values in `${DEVICE_AUTHORIZER_VALID_TOKENS}` -> Defined AWS SSM Parameter Store
- Body:
    - `{"thingName": ${THING_NAME}, "version": "${VERSION}"}`
    

**Default AWS IoT resources**
---

These resources by name or ARN are stored in the AWS Parameter Store SSM construct.

- `AWS_ROOT_CA.PREFERRED` and `AWS_ROOT_CA.BACKUP` -> AWS IoT root CA endpoints, a preferred one and a backup one.
- `POLICIES.$TYPE.name` -> AWS IoT Thing Policy based on Thing Type name.
- `ATTRIBUTES.$TYPE.[].name` -> AWS IoT Thing Type Attributes based on Thing Type name.

- AWS IoT Policy Sample:
    - Should be created on the console and managed by that or by boto3. Not recommendable to manage using Cloudformation if naming is required.
    - Name should be added to `cdk.json` in `ssm.string_value.POLICIES` section.
    - If using project with defaults. Use as name -> `multa_backend_policy_dev`
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iot:Connect"
      ],
      "Resource": [
        "arn:aws:iot:us-east-1:${ACCOUNT_ID}:client/${iot:Connection.Thing.ThingName}"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Publish"
      ],
      "Resource": [
        "arn:aws:iot:us-east-1:${ACCOUNT_ID}:topic/tlm/*/${iot:Connection.Thing.ThingName}/d2c",
        "arn:aws:iot:us-east-1:${ACCOUNT_ID}:topic/cmd/*/${iot:Connection.Thing.ThingName}/d2c",
        "arn:aws:iot:us-east-1:${ACCOUNT_ID}:topic/$aws/things/${iot:Connection.Thing.ThingName}/shadow/get",
        "arn:aws:iot:us-east-1:${ACCOUNT_ID}:topic/$aws/things/${iot:Connection.Thing.ThingName}/shadow/update",
        "arn:aws:iot:us-east-1:${ACCOUNT_ID}:topic/$aws/things/${iot:Connection.Thing.ThingName}/defender/metrics/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Subscribe"
      ],
      "Resource": [
        "arn:aws:iot:us-east-1:${ACCOUNT_ID}:topicfilter/cmd/*/${iot:Connection.Thing.ThingName}/c2d",
        "arn:aws:iot:us-east-1:${ACCOUNT_ID}:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/shadow/update/*",
        "arn:aws:iot:us-east-1:${ACCOUNT_ID}:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/shadow/get/*",
        "arn:aws:iot:us-east-1:${ACCOUNT_ID}:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/defender/metrics/*/accepted",
        "arn:aws:iot:us-east-1:${ACCOUNT_ID}:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/defender/metrics/*/rejected"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Receive"
      ],
      "Resource": [
        "arn:aws:iot:us-east-1:${ACCOUNT_ID}:topic/$aws/things/${iot:Connection.Thing.ThingName}/shadow/update/*",
        "arn:aws:iot:us-east-1:${ACCOUNT_ID}:topic/$aws/things/${iot:Connection.Thing.ThingName}/shadow/get/*",
        "arn:aws:iot:us-east-1:${ACCOUNT_ID}:topic/$aws/things/${iot:Connection.Thing.ThingName}/defender/metrics/*/accepted",
        "arn:aws:iot:us-east-1:${ACCOUNT_ID}:topic/$aws/things/${iot:Connection.Thing.ThingName}/defender/metrics/*/rejected"
      ]
    }
  ]
}
```
    
**Project Extension**
---

In order to add new modules or lambda functions to the project, either Authorizer or Registration Lambdas, base structure is the same:

- `applications` module contains the lambda functions and those are formed by `components`

- `components` contain the Classes that will be used in `applications` and those are formed by `handlers` Classes and functions.

- `handlers` are the base Classes and functions that will execute authorization, validation, registration, etc.

Finally, modify the configuration in `cdk.json` to point to different Lambda functions other that the defaults.


**How to Contribute**
---

1. Clone repo and create a new branch: `$ git checkout https://github.com/u93/aws-iot-certificate-vending-machine -b ${BRANCH_NAME}`.
2. Make changes and test
3. Submit Pull Request with comprehensive description of changes