class IoTBotoError(Exception):
    """Raise if there is an error with AWS IoT boto3 call"""


class WrongindexingConfiguration(Exception):
    """Raise if a wrong indexing configuration is passed to the registry setup functionality"""


class WrongBoto3Response(Exception):
    """Raise if a boto3 call does not returns 200 OK as HTTPStatussCode"""


class PolicyDetachError(Exception):
    """Raised if issue detaching a policy from a principal, like a X.509 certificate"""


class QueryError(Exception):
    """Raised if the desired query does not perform correctly"""

    pass


class ThingNotExists(Exception):
    """Raised if described thing operation fails, probably because thing does not exists."""

    pass


class UnauthorizedThing(Exception):
    """Raised if a thing trying to register passes an invalid authorization hash"""

    pass
