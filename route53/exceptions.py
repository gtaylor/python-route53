
class Route53Error(Exception):
    """
    Base class for all Petfinder API exceptions. Mostly here to allow end
    users to catch all Petfinder exceptions.
    """

    pass


class RecordDoesNotExistError(Route53Error):
    """
    Raised when querying for a record that does not exist.
    """

    pass