from route53.change_set import ChangeSet
from route53.exceptions import AlreadyDeletedError
from route53.resource_record_set import AResourceRecordSet, AAAAResourceRecordSet, CNAMEResourceRecordSet, MXResourceRecordSet, NSResourceRecordSet, PTRResourceRecordSet, SOAResourceRecordSet, SPFResourceRecordSet, SRVResourceRecordSet, TXTResourceRecordSet

class HostedZone(object):
    """
    A hosted zone is a collection of resource record sets hosted by Route 53.
    Like a traditional DNS zone file, a hosted zone represents a collection of
    resource record sets that are managed together under a single domain name.
    Each hosted zone has its own metadata and configuration information.

    .. warning:: Do not instantiate this directly yourself. Go through
        one of the methods on :py:class:`route53.connection.Route53Connection`.
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
        # This is set to True when this HostedZone has been deleted in Route53.
        self._is_deleted = False

    def __str__(self):
        return '<HostedZone: %s -- %s>' % (self.name, self.id)

    @property
    def nameservers(self):
        """
        :rtype: list
        :returns: A list of nameserver strings for this hosted zone.
        """

        # If this HostedZone was instantiated by ListHostedZones, the nameservers
        # attribute didn't get populated. If the user requests it, we'll
        # lazy load by querying it in after the fact. It's safe to cache like
        # this since  these nameserver values won't change.
        if not self._nameservers:
            # We'll just snatch the nameserver values from a fresh copy
            # via GetHostedZone.
            hosted_zone = self.connection.get_hosted_zone_by_id(self.id)
            self._nameservers = hosted_zone._nameservers

        return self._nameservers

    @property
    def record_sets(self):
        """
        Queries for the Resource Record Sets that are under this HostedZone.
        This is typically the way to go to find specific record sets, or
        to list them all.

        We don't currently implement any filtering convenience method,
        since it is very easy to do this yourself, catered to your own needs.
        For example, if you find your match, you may choose to stop iterating
        on the generator, potentially saving yourself extra API queries
        (behind the scenes).

        .. warning:: This result set can get pretty large if you have a ton
            of records.

        :rtype: generator
        :returns: A generator of ResourceRecordSet sub-classes.
        """

        for rrset in self.connection._list_resource_record_sets_by_zone_id(self.id):
            yield rrset

    def delete(self, force=False):
        """
        Deletes this hosted zone. After this method is ran, you won't be able
        to add records, or do anything else with the zone. You'd need to
        re-create it, as zones are read-only after creation.

        :keyword bool force: If ``True``, delete the
            :py:class:`HostedZone <route53.hosted_zone.HostedZone>`, even if it
            means nuking all associated record sets. If ``False``, an
            exception is raised if this
            :py:class:`HostedZone <route53.hosted_zone.HostedZone>`
            has record sets.
        :rtype: dict
        :returns: A dict of change info, which contains some details about
            the request.
        """

        self._halt_if_already_deleted()

        if force:
            # Forcing deletion by cleaning up all record sets first. We'll
            # do it all in one change set.
            cset = ChangeSet(connection=self.connection, hosted_zone_id=self.id)

            for rrset in self.record_sets:
                # You can delete a HostedZone if there are only SOA and NS
                # entries left. So delete everything but SOA/NS entries.
                if rrset.rrset_type not in ['SOA', 'NS']:
                    cset.add_change('DELETE', rrset)

            if cset.deletions or cset.creations:
                # Bombs away.
                self.connection._change_resource_record_sets(cset)

        # Now delete the HostedZone.
        retval = self.connection.delete_hosted_zone_by_id(self.id)

        # Used to protect against modifying a deleted HostedZone.
        self._is_deleted = True

        return retval

    def _halt_if_already_deleted(self):
        """
        Convenience method used to raise an AlreadyDeletedError exception if
        this HostedZone has been deleted.

        :raises: AlreadyDeletedError
        """

        if self._is_deleted:
            raise AlreadyDeletedError("Can't manipulate a deleted zone.")

    def _add_record(self, record_set_class, name, values, ttl=60, weight=None,
                    region=None,set_identifier=None, alias_hosted_zone_id=None,
                    alias_dns_name=None):
        """
        Convenience method for creating ResourceRecordSets. Most of the calls
        are basically the same, this saves on repetition.

        :rtype: tuple
        :returns: A tuple in the form of ``(rrset, change_info)``, where
            ``rrset`` is the newly created ResourceRecordSet sub-class
             instance.
        """

        self._halt_if_already_deleted()

        rrset_kwargs = dict(
            connection=self.connection,
            zone_id=self.id,
            name=name,
            ttl=ttl,
            records=values,
            weight=weight,
            region=region,
            set_identifier=set_identifier,
            )

        if alias_hosted_zone_id or alias_dns_name:
            rrset_kwargs.update(dict(
                alias_hosted_zone_id=alias_hosted_zone_id,
                alias_dns_name=alias_dns_name
            ))

        rrset = record_set_class(**rrset_kwargs)

        cset = ChangeSet(connection=self.connection, hosted_zone_id=self.id)
        cset.add_change('CREATE', rrset)

        change_info = self.connection._change_resource_record_sets(cset)

        return rrset, change_info

    def create_a_record(self, name, values, ttl=60, weight=None, region=None,
                     set_identifier=None, alias_hosted_zone_id=None,
                     alias_dns_name=None):
        """
        Creates and returns an A record attached to this hosted zone.

        :param str name: The fully qualified name of the record to add.
        :param list values: A list of value strings for the record.
        :keyword int ttl: The time-to-live of the record (in seconds).
        :keyword int weight: *For weighted record sets only*. Among resource record
            sets that have the same combination of DNS name and type, a value
            that determines what portion of traffic for the current resource
            record set is routed to the associated location. Ranges from 0-255.
        :keyword str region: *For latency-based record sets*. The Amazon EC2 region
            where the resource that is specified in this resource record set
            resides.
        :keyword str set_identifier: *For weighted and latency resource record
            sets only*. An identifier that differentiates among multiple
            resource record sets that have the same combination of DNS name
            and type. 1-128 chars.
        :keyword str alias_hosted_zone_id: Alias A records have this specified.
            It appears to be the hosted zone ID for the ELB the Alias points at.
        :keyword str alias_dns_name: Alias A records have this specified. It is
            the DNS name for the ELB that the Alias points to.
        :rtype: tuple
        :returns: A tuple in the form of ``(rrset, change_info)``, where
            ``rrset`` is the newly created
            :py:class:`AResourceRecordSet <route53.resource_record_set.AResourceRecordSet>`
            instance.
        """

        self._halt_if_already_deleted()

        # Grab the params/kwargs here for brevity's sake.
        values = locals()
        del values['self']

        return self._add_record(AResourceRecordSet, **values)

    def create_aaaa_record(self, name, values, ttl=60, weight=None, region=None,
                        set_identifier=None):
        """
        Creates an AAAA record attached to this hosted zone.

        :param str name: The fully qualified name of the record to add.
        :param list values: A list of value strings for the record.
        :keyword int ttl: The time-to-live of the record (in seconds).
        :keyword int weight: *For weighted record sets only*. Among resource record
            sets that have the same combination of DNS name and type, a value
            that determines what portion of traffic for the current resource
            record set is routed to the associated location. Ranges from 0-255.
        :keyword str region: *For latency-based record sets*. The Amazon EC2 region
            where the resource that is specified in this resource record set
            resides.
        :keyword str set_identifier: *For weighted and latency resource record
            sets only*. An identifier that differentiates among multiple
            resource record sets that have the same combination of DNS name
            and type. 1-128 chars.
        :rtype: tuple
        :returns: A tuple in the form of ``(rrset, change_info)``, where
            ``rrset`` is the newly created AAAAResourceRecordSet instance.
        """

        self._halt_if_already_deleted()

        # Grab the params/kwargs here for brevity's sake.
        values = locals()
        del values['self']

        return self._add_record(AAAAResourceRecordSet, **values)

    def create_cname_record(self, name, values, ttl=60, weight=None, region=None,
                           set_identifier=None):
        """
        Creates a CNAME record attached to this hosted zone.

        :param str name: The fully qualified name of the record to add.
        :param list values: A list of value strings for the record.
        :keyword int ttl: The time-to-live of the record (in seconds).
        :keyword int weight: *For weighted record sets only*. Among resource record
            sets that have the same combination of DNS name and type, a value
            that determines what portion of traffic for the current resource
            record set is routed to the associated location. Ranges from 0-255.
        :keyword str region: *For latency-based record sets*. The Amazon EC2 region
            where the resource that is specified in this resource record set
            resides.
        :keyword str set_identifier: *For weighted and latency resource record
            sets only*. An identifier that differentiates among multiple
            resource record sets that have the same combination of DNS name
            and type. 1-128 chars.
        :rtype: tuple
        :returns: A tuple in the form of ``(rrset, change_info)``, where
            ``rrset`` is the newly created CNAMEResourceRecordSet instance.
        """

        self._halt_if_already_deleted()

        # Grab the params/kwargs here for brevity's sake.
        values = locals()
        del values['self']

        return self._add_record(CNAMEResourceRecordSet, **values)

    def create_mx_record(self, name, values, ttl=60):
        """
        Creates a MX record attached to this hosted zone.

        :param str name: The fully qualified name of the record to add.
        :param list values: A list of value strings for the record.
        :keyword int ttl: The time-to-live of the record (in seconds).
        :rtype: tuple
        :returns: A tuple in the form of ``(rrset, change_info)``, where
            ``rrset`` is the newly created MXResourceRecordSet instance.
        """

        self._halt_if_already_deleted()

        # Grab the params/kwargs here for brevity's sake.
        values = locals()
        del values['self']

        return self._add_record(MXResourceRecordSet, **values)

    def create_ns_record(self, name, values, ttl=60):
        """
        Creates a NS record attached to this hosted zone.

        :param str name: The fully qualified name of the record to add.
        :param list values: A list of value strings for the record.
        :keyword int ttl: The time-to-live of the record (in seconds).
        :rtype: tuple
        :returns: A tuple in the form of ``(rrset, change_info)``, where
            ``rrset`` is the newly created NSResourceRecordSet instance.
        """

        self._halt_if_already_deleted()

        # Grab the params/kwargs here for brevity's sake.
        values = locals()
        del values['self']

        return self._add_record(NSResourceRecordSet, **values)

    def create_ptr_record(self, name, values, ttl=60):
        """
        Creates a PTR record attached to this hosted zone.

        :param str name: The fully qualified name of the record to add.
        :param list values: A list of value strings for the record.
        :keyword int ttl: The time-to-live of the record (in seconds).
        :rtype: tuple
        :returns: A tuple in the form of ``(rrset, change_info)``, where
            ``rrset`` is the newly created PTRResourceRecordSet instance.
        """

        self._halt_if_already_deleted()

        # Grab the params/kwargs here for brevity's sake.
        values = locals()
        del values['self']

        return self._add_record(PTRResourceRecordSet, **values)

    def create_spf_record(self, name, values, ttl=60):
        """
        Creates a SPF record attached to this hosted zone.

        :param str name: The fully qualified name of the record to add.
        :param list values: A list of value strings for the record.
        :keyword int ttl: The time-to-live of the record (in seconds).
        :rtype: tuple
        :returns: A tuple in the form of ``(rrset, change_info)``, where
            ``rrset`` is the newly created SPFResourceRecordSet instance.
        """

        self._halt_if_already_deleted()

        # Grab the params/kwargs here for brevity's sake.
        values = locals()
        del values['self']

        return self._add_record(SPFResourceRecordSet, **values)

    def create_srv_record(self, name, values, ttl=60):
        """
        Creates a SRV record attached to this hosted zone.

        :param str name: The fully qualified name of the record to add.
        :param list values: A list of value strings for the record.
        :keyword int ttl: The time-to-live of the record (in seconds).
        :rtype: tuple
        :returns: A tuple in the form of ``(rrset, change_info)``, where
            ``rrset`` is the newly created SRVResourceRecordSet instance.
        """

        self._halt_if_already_deleted()

        # Grab the params/kwargs here for brevity's sake.
        values = locals()
        del values['self']

        return self._add_record(SRVResourceRecordSet, **values)

    def create_txt_record(self, name, values, ttl=60, weight=None, region=None,
                          set_identifier=None):
        """
        Creates a TXT record attached to this hosted zone.

        :param str name: The fully qualified name of the record to add.
        :param list values: A list of value strings for the record.
        :keyword int ttl: The time-to-live of the record (in seconds).
        :keyword int weight: *For weighted record sets only*. Among resource record
            sets that have the same combination of DNS name and type, a value
            that determines what portion of traffic for the current resource
            record set is routed to the associated location. Ranges from 0-255.
        :keyword str region: *For latency-based record sets*. The Amazon EC2 region
            where the resource that is specified in this resource record set
            resides.
        :keyword str set_identifier: *For weighted and latency resource record
            sets only*. An identifier that differentiates among multiple
            resource record sets that have the same combination of DNS name
            and type. 1-128 chars.
        :rtype: tuple
        :returns: A tuple in the form of ``(rrset, change_info)``, where
            ``rrset`` is the newly created TXTResourceRecordSet instance.
        """

        self._halt_if_already_deleted()

        # Grab the params/kwargs here for brevity's sake.
        values = locals()
        del values['self']

        return self._add_record(TXTResourceRecordSet, **values)