from route53.change_set import ChangeSet
from route53.exceptions import Route53Error

class ResourceRecordSet(object):
    """
    A Resource Record Set is an entry within a Hosted Zone. These can be
    anything from TXT entries, to A entries, to CNAMEs.

    .. warning:: Do not instantiate this directly yourself. Go through
        one of the methods on:py:class:`route53.connection.Route53Connection`.
    """

    # Override this in your sub-class.
    rrset_type = None

    def __init__(self, connection, zone_id, name, ttl, records, weight=None,
                 region=None, set_identifier=None):
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
        :keyword int weight: For weighted record sets only. Among resource record
            sets that have the same combination of DNS name and type, a value
            that determines what portion of traffic for the current resource
            record set is routed to the associated location. Ranges from 0-255.
        :keyword str region: For latency-based record sets. The Amazon EC2 region
            where the resource that is specified in this resource record set
            resides.
        :keyword str set_identifier: For weighted and latency resource record
            sets only. An identifier that differentiates among multiple
            resource record sets that have the same combination of DNS name
            and type. 1-128 chars.
        """

        self.connection = connection
        self.zone_id = zone_id
        self.name = name
        self.ttl = int(ttl) if ttl else None
        self.records = records
        self.region = region
        self.weight = weight
        self.set_identifier = set_identifier

        # Keep track of the initial values for this record set. We use this
        # to detect changes that need saving.
        self._initial_vals = dict(
            connection=connection,
            zone_id=zone_id,
            name=name,
            ttl=ttl,
            records=records[:],
            region=region,
            weight=weight,
            set_identifier=set_identifier,
        )

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)

    @property
    def hosted_zone(self):
        """
        Queries for this record set's HostedZone.

        .. note:: This is not cached, it will always return the latest
            data from the Route 53 API.

        :rtype: :py:class:`HostedZone <route53.hosted_zone.HostedZone>`
        :returns: The matching :py:class:`HostedZone <route53.hosted_zone.HostedZone>`
            for this record set.
        """

        return self.connection.get_hosted_zone_by_id(self.zone_id)

    def is_modified(self):
        """
        Determines whether this record set has been modified since the
        last retrieval or save.

        :rtype: bool
        :returns: ``True` if the record set has been modified,
            and ``False`` if not.
        """

        for key, val in self._initial_vals.items():
            if getattr(self, key) != val:
                # One of the initial values doesn't match, we know
                # this object has been touched.
                return True

        return False

    def delete(self):
        """
        Deletes this record set.
        """

        cset = ChangeSet(connection=self.connection, hosted_zone_id=self.zone_id)
        cset.add_change('DELETE', self)

        return self.connection._change_resource_record_sets(cset)

    def save(self):
        """
        Saves any changes to this record set.
        """

        cset = ChangeSet(connection=self.connection, hosted_zone_id=self.zone_id)
        # Record sets can't actually be modified. You have to delete the
        # existing one and create a new one. Since this happens within a single
        # change set, it appears that the values were modified, when instead
        # the whole thing is replaced.
        cset.add_change('DELETE', self)
        cset.add_change('CREATE', self)
        retval = self.connection._change_resource_record_sets(cset)

        # Now copy the current attribute values on this instance to
        # the initial_vals dict. This will re-set the modification tracking.
        for key, val in self._initial_vals.items():
            self._initial_vals[key] = getattr(self, key)

        return retval

    def is_alias_record_set(self):
        """
        Checks whether this is an A record in Alias mode.

        :rtype: bool
        :returns: ``True`` if this is an A record in Alias mode, and
            ``False`` otherwise.
        """

        # AResourceRecordSet overrides this. Everyone else is False.
        return False


class AResourceRecordSet(ResourceRecordSet):
    """
    Specific A record class. There are two kinds of A records:

    * Regular A records.
    * Alias A records. These point at an ELB instance instead of an IP.

    Create these via
    :py:meth:`HostedZone.create_a_record <route53.hosted_zone.HostedZone.create_a_record>`.
    Retrieve them via
    :py:meth:`HostedZone.record_sets <route53.hosted_zone.HostedZone.record_sets>`.
    """

    rrset_type = 'A'

    def __init__(self, alias_hosted_zone_id=None, alias_dns_name=None, *args, **kwargs):
        """
        :keyword str alias_hosted_zone_id: Alias A records have this specified.
            It appears to be the hosted zone ID for the ELB the Alias points at.
        :keyword str alias_dns_name: Alias A records have this specified. It is
            the DNS name for the ELB that the Alias points to.
        """

        super(AResourceRecordSet, self).__init__(*args, **kwargs)

        self.alias_hosted_zone_id = alias_hosted_zone_id
        self.alias_dns_name = alias_dns_name

        # Keep track of the initial values for this record set. We use this
        # to detect changes that need saving.
        self._initial_vals.update(
            dict(
                alias_hosted_zone_id=alias_hosted_zone_id,
                alias_dns_name=alias_dns_name,
            )
        )

    def is_alias_record_set(self):
        """
        Checks whether this is an A record in Alias mode.

        :rtype: bool
        :returns: ``True`` if this is an A record in Alias mode, and
            ``False`` otherwise.
        """

        return self.alias_hosted_zone_id or self.alias_dns_name


class AAAAResourceRecordSet(AResourceRecordSet):
    """
    Specific AAAA record class. Create these via
    :py:meth:`HostedZone.create_aaaa_record <route53.hosted_zone.HostedZone.create_aaaa_record>`.
    Retrieve them via
    :py:meth:`HostedZone.record_sets <route53.hosted_zone.HostedZone.record_sets>`.
    """

    rrset_type = 'AAAA'


class CNAMEResourceRecordSet(ResourceRecordSet):
    """
    Specific CNAME record class. Create these via
    :py:meth:`HostedZone.create_cname_record <route53.hosted_zone.HostedZone.create_cname_record>`.
    Retrieve them via
    :py:meth:`HostedZone.record_sets <route53.hosted_zone.HostedZone.record_sets>`.
    """

    rrset_type = 'CNAME'

    def __init__(self, alias_hosted_zone_id=None, alias_dns_name=None, *args, **kwargs):
        """
        :keyword str alias_hosted_zone_id: Alias CNAME records have this specified.
            It appears to be the hosted zone ID for the ELB the Alias points at.
        :keyword str alias_dns_name: Alias CNAME records have this specified. It is
            the DNS name for the ELB that the Alias points to.
        """

        super(CNAMEResourceRecordSet, self).__init__(*args, **kwargs)

        self.alias_hosted_zone_id = alias_hosted_zone_id
        self.alias_dns_name = alias_dns_name

        # Keep track of the initial values for this record set. We use this
        # to detect changes that need saving.
        self._initial_vals.update(
            dict(
                alias_hosted_zone_id=alias_hosted_zone_id,
                alias_dns_name=alias_dns_name,
            )
        )

    def is_alias_record_set(self):
        """
        Checks whether this is an A record in Alias mode.

        :rtype: bool
        :returns: ``True`` if this is an A record in Alias mode, and
            ``False`` otherwise.
        """

        return self.alias_hosted_zone_id or self.alias_dns_name


class MXResourceRecordSet(ResourceRecordSet):
    """
    Specific MX record class. Create these via
    :py:meth:`HostedZone.create_mx_record <route53.hosted_zone.HostedZone.create_mx_record>`.
    Retrieve them via
    :py:meth:`HostedZone.record_sets <route53.hosted_zone.HostedZone.record_sets>`.
    """

    rrset_type = 'MX'


class NSResourceRecordSet(ResourceRecordSet):
    """
    Specific NS record class. Create these via
    :py:meth:`HostedZone.create_ns_record <route53.hosted_zone.HostedZone.create_ns_record>`.
    Retrieve them via
    :py:meth:`HostedZone.record_sets <route53.hosted_zone.HostedZone.record_sets>`.
    """

    rrset_type = 'NS'


class PTRResourceRecordSet(ResourceRecordSet):
    """
    Specific PTR record class. Create these via
    :py:meth:`HostedZone.create_ptr_record <route53.hosted_zone.HostedZone.create_ptr_record>`.
    Retrieve them via
    :py:meth:`HostedZone.record_sets <route53.hosted_zone.HostedZone.record_sets>`.
    """

    rrset_type = 'PTR'


class SOAResourceRecordSet(ResourceRecordSet):
    """
    Specific SOA record class. Retrieve these via
    :py:meth:`HostedZone.record_sets <route53.hosted_zone.HostedZone.record_sets>`.
    They can't be created.
    """

    rrset_type = 'SOA'

    def delete(self):
        """
        SOA records can't be created or deleted.
        """

        raise Route53Error("SOA records can't be created or deleted.")


class SPFResourceRecordSet(ResourceRecordSet):
    """
    Specific SPF record class. Create these via
    :py:meth:`HostedZone.create_spf_record <route53.hosted_zone.HostedZone.create_spf_record>`.
    Retrieve them via
    :py:meth:`HostedZone.record_sets <route53.hosted_zone.HostedZone.record_sets>`.
    """

    rrset_type = 'SPF'


class SRVResourceRecordSet(ResourceRecordSet):
    """
    Specific SRV record class. Create these via
    :py:meth:`HostedZone.create_srv_record <route53.hosted_zone.HostedZone.create_srv_record>`.
    Retrieve them via
    :py:meth:`HostedZone.record_sets <route53.hosted_zone.HostedZone.record_sets>`.
    """

    rrset_type = 'SRV'


class TXTResourceRecordSet(ResourceRecordSet):
    """
    Specific TXT record class. Create these via
    :py:meth:`HostedZone.create_txt_record <route53.hosted_zone.HostedZone.create_txt_record>`.
    Retrieve them via
    :py:meth:`HostedZone.record_sets <route53.hosted_zone.HostedZone.record_sets>`.
    """

    rrset_type = 'TXT'
