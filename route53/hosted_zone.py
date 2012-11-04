from route53.change_set import ChangeSet
from route53.exceptions import AlreadyDeletedError
from route53.resource_record_set import AResourceRecordSet

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
        # This is set to True when this HostedZone has been deleted in Route53.
        self._is_deleted = False

    def __str__(self):
        return '<HostedZone: %s -- %s>' % (self.name, self.id)

    @property
    def nameservers(self):
        """
        If this HostedZone was instantiated by ListHostedZones, the nameservers
        attribute didn't get populated. If the user requests it, we'll
        lazy load by querying it in after the fact. It's safe to cache like
        this since  these nameserver values won't change.

        :rtype: list
        :returns: A list of nameserver strings for this hosted zone.
        """

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

        .. warning:: This result set can get pretty large if you have a ton
            of records.

        :rtype: generator
        :returns: A generator of ResourceRecordSet sub-classes.
        """

        for rrset in self.connection.list_resource_record_sets_by_zone_id(self.id):
            yield rrset

    def delete(self, force=False):
        """
        Deletes this hosted zone. After this method is ran, you won't be able
        to add records, or do anything else with the zone. You'd need to
        re-create it, as zones are read-only after creation.

        :keyword bool force: If ``True``, delete the HostedZone, even if it
            means nuking all associated record sets. If ``False``, an
            exception is raised if this HostedZone has record sets.
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

    def add_a_record(self, name, values, ttl=60):
        """
        Adds an A record to the hosted zone.

        :param str name: The fully qualified name of the record to add.
        :param list values: A list of value strings for the record.
        :keyword int ttl: The time-to-live of the record (in seconds).
        :rtype: tuple
        :returns: A tuple in the form of ``(rrset, change_info)``, where
            ``rrset`` is the newly created AResourceRecordSet instance.
        """

        self._halt_if_already_deleted()

        rrset = AResourceRecordSet(
            connection=self.connection,
            zone_id=self.id,
            name=name,
            ttl=ttl,
            records=values,
        )

        cset = ChangeSet(connection=self.connection, hosted_zone_id=self.id)
        cset.add_change('CREATE', rrset)

        change_info = self.connection._change_resource_record_sets(cset)

        return rrset, change_info