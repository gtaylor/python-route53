"""
The top-level route53 module is used as the default entry point to
python-route53's functionality. You'll want to go through the :py:func:`connect`
function to get a
:py:class:`Route53Connection <route53.connection.Route53Connection>`
instance to work with the Route 53 API.
"""

VERSION = '1.0'

def connect(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """
    Instantiates and returns a :py:class:`route53.connection.Route53Connection`
    instance, which is how you'll start your interactions with the Route 53
    API.

    :keyword str aws_access_key_id: Your AWS Access Key ID
    :keyword str aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :py:class:`route53.connection.Route53Connection`
    :return: A connection to Amazon's Route 53
    """

    from route53.connection import Route53Connection
    return Route53Connection(
        aws_access_key_id,
        aws_secret_access_key,
        **kwargs
    )