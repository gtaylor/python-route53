
class ResourceRecordSet(object):
    """
    A Resource Record Set is an entry within a Hosted Zone. These can be
    anything from TXT entries, to A entries, to CNAMEs.

    .. warning:: Do not instantiate this directly yourself. Go through
        one of the methods on:py:class:``route53.connection.Route53Connection`.
    """

    def __init__(self, connection, zone_id, name, rrset_type, ttl, records):
        """
        :param Route53Connection connection: The connection instance that
            was used to query the Route53 API, leading to this object's
            creation.
        :param str zone_id: The zone ID of the HostedZone that this
            resource record set belongs to.
        :param str name: The fully qualified name of the resource record set.
        :param int ttl: The time-to-live. A Aliases have no TTL, so this can
            be None in that case.
        :param list records: A list of resource record strings. For some
            types (A entries that are Aliases), this is an empty list.
        """

        self.connection = connection
        self.zone_id = zone_id
        self.name = name
        self.rrset_type = rrset_type
        self.ttl = int(ttl) if ttl else None
        self.records = records

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)

    @property
    def hosted_zone(self):
        """
        Queries for this record set's HostedZone.

        :rtype: HostedZone
        :returns: The matching HostedZone for this record set.
        """

        return self.connection.get_hosted_zone_by_id(self.zone_id)


class AResourceRecordSet(ResourceRecordSet):
    """
    Specific A record class.
    """

    def __init__(self, alias_hosted_zone_id=None, alias_dns_name=None, *args, **kwargs):
        self.alias_hosted_zone_id = alias_hosted_zone_id
        self.alias_dns_name = alias_dns_name

        super(AResourceRecordSet, self).__init__(*args, **kwargs)


class AAAAResourceRecordSet(ResourceRecordSet):
    """
    Specific AAAA record class.
    """

    pass


class CNAMEResourceRecordSet(ResourceRecordSet):
    """
    Specific CNAME record class.
    """

    pass


class MXResourceRecordSet(ResourceRecordSet):
    """
    Specific MX record class.
    """

    pass


class NSResourceRecordSet(ResourceRecordSet):
    """
    Specific NS record class.
    """

    pass


class PTRResourceRecordSet(ResourceRecordSet):
    """
    Specific PTR record class.
    """

    pass


class SOAResourceRecordSet(ResourceRecordSet):
    """
    Specific SOA record class.
    """

    pass


class SPFResourceRecordSet(ResourceRecordSet):
    """
    Specific SPF record class.
    """

    pass


class SRVResourceRecordSet(ResourceRecordSet):
    """
    Specific SRV record class.
    """

    pass


class TXTResourceRecordSet(ResourceRecordSet):
    """
    Specific TXT record class.
    """

    pass
