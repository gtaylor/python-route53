
class Route53Error(Exception):
    """
    Base class for all Route53 API exceptions. Mostly here to allow end
    users to catch all Route53 exceptions.
    """

    pass


class AlreadyDeletedError(Route53Error):
    """
    Raised when the user tries to modify something on a hosted zone that
    has been deleted in Route53.
    """

    pass