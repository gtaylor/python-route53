
class HostedZone(object):
    """
    A hosted zone is a collection of resource record sets hosted by Route 53.
    Like a traditional DNS zone file, a hosted zone represents a collection of
    resource record sets that are managed together under a single domain name.
    Each hosted zone has its own metadata and configuration information.
    """

    def __init__(self, connection, id, name, caller_reference,
                 resource_record_set_count, comment):
        """
        :param Route53Connection connection: The connection instance that
            was used to query the Route53 API, leading to this object's
            creation.
        :param str id: Route53's unique ID for this hosted zone.
        :param str name: The name of the domain.
        :param str caller_reference: A unique string that identifies the
            request to create the hosted zone.
        :param int resource_record_set_count: The number of resource record
            sets in the hosted zone.
        """

        self.connection = connection
        self.id = id
        self.name = name
        self.caller_reference = caller_reference
        self.resource_record_set_count = int(resource_record_set_count)
        self.comment = comment
        self._nameservers = []

    @property
    def nameservers(self):
        # TODO: Lazy load these if they aren't set.
        return self._nameservers

    def __str__(self):
        return '<HostedZone: %s>' % self.name