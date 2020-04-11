import boto3

partial_name = "basic"
iot_client = boto3.client("iot")
thing_types = list()


response = iot_client.list_things(maxResults=1)
next_token = response.get("nextToken")
while next_token is not None:
    try:
        next_token = response.get("nextToken")
        print(next_token)
        if next_token is None:
            response = iot_client.list_things(maxResults=1)
        else:
            response = iot_client.list_things(maxResults=1, nextToken=next_token)
    except Exception as e:
        print(e)
        raise RuntimeError
    print(response)
    thing_types.extend(response["things"])

print(thing_types)

# results = [
#     thing_type["thingTypeName"] for thing_type in thing_types if partial_name in thing_type["thingTypeName"].lower()
# ]
#
# print(results[0])