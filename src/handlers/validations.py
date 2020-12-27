from marshmallow import Schema, fields, validates, ValidationError


class RequestAwsIoTThingSchema(Schema):
    thing_name = fields.Str(required=True, data_key="thingName")
    account_token = fields.Str(required=True, data_key="accountToken")
    version = fields.Str(required=True, data_key="version")


class RegisterAwsIoTThingSchema(Schema):
    thing_name = fields.Str(required=True, data_key="thingName")
    thing_type_name = fields.Str(required=True, data_key="thingTypeName")
    attribute_payload = fields.Dict(attributes=fields.Dict(), data_key="thingAttributes")

    # @validates("thing_type_name")
    # def thing_type_exists(self, value):
    #     # TODO: AT INIT, THE DEFAULT THING TYPES MUST BE CREATED OR LATER UPDATED BY CLI COMMAND
    #     if value not in thing_types:
    #         raise ValidationError("Thing type does not exists!")