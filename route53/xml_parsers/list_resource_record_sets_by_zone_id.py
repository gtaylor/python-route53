from route53.exceptions import Route53Error
from route53.resource_record_set import AResourceRecordSet, AAAAResourceRecordSet, CNAMEResourceRecordSet, MXResourceRecordSet, NSResourceRecordSet, PTRResourceRecordSet, SOAResourceRecordSet, SPFResourceRecordSet, SRVResourceRecordSet, TXTResourceRecordSet

# Maps ResourceRecordSet subtag names to kwargs in RRSet subclasses.
RRSET_TAG_TO_KWARG_MAP = {
    'Name': 'name',
    'TTL': 'ttl',
    'Weight': 'weight',
    'Region': 'region',
    'SetIdentifier': 'set_identifier',
}

# Maps the various ResourceRecordSet Types to various RRSet subclasses.
RRSET_TYPE_TO_RSET_SUBCLASS_MAP = {
    'A': AResourceRecordSet,
    'AAAA': AAAAResourceRecordSet,
    'CNAME': CNAMEResourceRecordSet,
    'MX': MXResourceRecordSet,
    'NS': NSResourceRecordSet,
    'PTR': PTRResourceRecordSet,
    'SOA': SOAResourceRecordSet,
    'SPF': SPFResourceRecordSet,
    'SRV': SRVResourceRecordSet,
    'TXT': TXTResourceRecordSet,
}

def parse_rrset_alias(e_alias):
    """
    Parses an Alias tag beneath a ResourceRecordSet, spitting out the two values
    found within. This is specific to A records that are set to Alias.

    :param lxml.etree._Element e_alias: An Alias tag beneath a ResourceRecordSet.
    :rtype: tuple
    :returns: A tuple in the form of ``(alias_hosted_zone_id, alias_dns_name)``.
    """

    alias_hosted_zone_id = e_alias.find('./{*}HostedZoneId').text
    alias_dns_name = e_alias.find('./{*}DNSName').text
    return alias_hosted_zone_id, alias_dns_name

def parse_rrset_record_values(e_resource_records):
    """
    Used to parse the various Values from the ResourceRecords tags on
    most rrset types.

    :param lxml.etree._Element e_resource_records: A ResourceRecords tag
        beneath a ResourceRecordSet.
    :rtype: list
    :returns: A list of resource record strings.
    """

    records = []

    for e_record in e_resource_records:
        for e_value in e_record:
            records.append(e_value.text)

    return records

def parse_rrset(e_rrset, connection, zone_id):
    """
    This a parser that allows the passing of any valid ResourceRecordSet
    tag. It will spit out the appropriate ResourceRecordSet object for the tag.

    :param lxml.etree._Element e_rrset: The root node of the etree parsed
        response from the API.
    :param Route53Connection connection: The connection instance used to
        query the API.
    :param str zone_id: The zone ID of the HostedZone these rrsets belong to.
    :rtype: ResourceRecordSet
    :returns: An instantiated ResourceRecordSet object.
    """

    # This dict will be used to instantiate a ResourceRecordSet instance to yield.
    kwargs = {
        'connection': connection,
        'zone_id': zone_id,
    }
    rrset_type = None

    for e_field in e_rrset:
        # Cheesy way to strip off the namespace.
        tag_name = e_field.tag.split('}')[1]
        field_text = e_field.text

        if tag_name == 'Type':
            # Need to store this to determine which ResourceRecordSet
            # subclass to instantiate.
            rrset_type = field_text
            continue
        elif tag_name == 'AliasTarget':
            # A records have some special field values we need.
            alias_hosted_zone_id, alias_dns_name = parse_rrset_alias(e_field)
            kwargs['alias_hosted_zone_id'] = alias_hosted_zone_id
            kwargs['alias_dns_name'] = alias_dns_name
            # Alias A entries have no TTL.
            kwargs['ttl'] = None
            continue
        elif tag_name == 'ResourceRecords':
            kwargs['records'] = parse_rrset_record_values(e_field)
            continue

        # Map the XML tag name to a kwarg name.
        kw_name = RRSET_TAG_TO_KWARG_MAP[tag_name]
        # This will be the key/val pair used to instantiate the
        # ResourceRecordSet instance.
        kwargs[kw_name] = field_text

    if not rrset_type:
        raise Route53Error("No Type tag found in ListResourceRecordSetsResponse.")

    if 'records' not in kwargs:
        # Not all rrsets have records.
        kwargs['records'] = []

    RRSetSubclass = RRSET_TYPE_TO_RSET_SUBCLASS_MAP[rrset_type]
    return RRSetSubclass(**kwargs)

def list_resource_record_sets_by_zone_id_parser(e_root, connection, zone_id):
    """
    Parses the API responses for the
    :py:meth:`route53.connection.Route53Connection.list_resource_record_sets_by_zone_id`
    method.

    :param lxml.etree._Element e_root: The root node of the etree parsed
        response from the API.
    :param Route53Connection connection: The connection instance used to
        query the API.
    :param str zone_id: The zone ID of the HostedZone these rrsets belong to.
    :rtype: ResourceRecordSet
    :returns: A generator of fully formed ResourceRecordSet instances.
    """

    # The rest of the list pagination tags are handled higher up in the stack.
    # We'll just worry about the ResourceRecordSets tag, which has
    # ResourceRecordSet tags nested beneath it.
    e_rrsets = e_root.find('./{*}ResourceRecordSets')

    for e_rrset in e_rrsets:
        yield parse_rrset(e_rrset, connection, zone_id)
