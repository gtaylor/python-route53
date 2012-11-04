import route53
from .credentials import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

def get_route53_connection():
    """
    All unit tests go through here for Route53Connection objects.

    :rtype: Route53Connection
    """

    return route53.connect(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )