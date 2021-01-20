from handlers.utils import Logger
from src.lambda_register import lambda_handler as register_handler


# Import Project Logger
project_logger = Logger()
logger = project_logger.get_logger()

fake_wrong_lambda_event = {"httpMethod": "POST", "body": "{}"}
fake_lambda_event = {"httpMethod": "POST", "body": '{"thingName":"Test12","version":"1"}'}

response = register_handler(event=fake_lambda_event, context={})