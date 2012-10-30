
class HostedZone(object):
    """
    A hosted zone is a collection of resource record sets hosted by Route 53.
    Like a traditional DNS zone file, a hosted zone represents a collection of
    resource record sets that are managed together under a single domain name.
    Each hosted zone has its own metadata and configuration information.

    .. warning:: Do not instantiate this directly yourself. Go through
        one of the methods on:py:class:``route53.connection.Route53Connection`.
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

        # Don't access this directly, we use it for lazy loading.
        self._nameservers = []

    @property
    def nameservers(self):
        """
        If this HostedZone was instantiated by ListHostedZones, the nameservers
        attribute didn't get populated. If the user requests it, we'll
        lazy load it in.

        :rtype: list
        :returns: A list of nameserver strings for this hosted zone.
        """

        if not self._nameservers:
            # We'll just snatch the nameserver values from a fresh copy
            # via GetHostedZone.
            hosted_zone = self.connection.get_hosted_zone_by_id(self.id)
            self._nameservers = hosted_zone._nameservers

        return self._nameservers

    def __str__(self):
        return '<HostedZone: %s -- %s>' % (self.name, self.id)