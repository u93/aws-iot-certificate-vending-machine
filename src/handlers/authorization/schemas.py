from marshmallow import Schema, fields, validates_schema, ValidationError


class RequestRegistrationAuthorizationSchema(Schema):
    authorization_token = fields.Str(required=True, data_key="authorizationToken")
    method_arn = fields.Str(required=True, data_key="methodArn")
    type = fields.Str(required=True, data_key="type")


class RequestRegistrationAuthorizationTokenSchema(Schema):
    @validates_schema
    def authorization_token_valid(self, data: dict, token_length: int, token_prefix: str):
        split_payload = data["authorizationToken"].split(" ")
        if len(split_payload) != token_length:
            raise ValidationError("Invalid token format... Not proper length")

        token_identifier = split_payload[0]
        if token_identifier != token_prefix:
            raise ValidationError("Invalid token format... Not authorized prefix")


class RequestAwsIoTThingSchema(Schema):
    thing_name = fields.Str(required=True, data_key="thingName")
    account_token = fields.Str(required=True, data_key="accountToken")
    version = fields.Str(required=True, data_key="version")


class RegisterAwsIoTThingSchema(Schema):
    thing_name = fields.Str(required=True, data_key="thingName")
    thing_type_name = fields.Str(required=True, data_key="thingTypeName")
    attribute_payload = fields.Dict(attributes=fields.Dict(), data_key="thingAttributes")
