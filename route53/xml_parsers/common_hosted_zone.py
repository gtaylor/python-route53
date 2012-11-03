"""
Contains a parser for HostedZone tags. These are used in several kinds of
XML responses (ListHostedZones and CreateHostedZone, for example).
"""

from route53.hosted_zone import HostedZone

# This dict maps tag names in the API response to a kwarg key used to
# instantiate HostedZone instances.
HOSTED_ZONE_TAG_TO_KWARG_MAP = {
    'Id': 'id',
    'Name': 'name',
    'CallerReference': 'caller_reference',
    'ResourceRecordSetCount': 'resource_record_set_count',
}

def parse_hosted_zone(e_zone, connection):
    """
    This a common parser that allows the passing of any valid HostedZone
    tag. It will spit out the appropriate HostedZone object for the tag.

    :param lxml.etree._Element e_zone: The root node of the etree parsed
        response from the API.
    :param Route53Connection connection: The connection instance used to
        query the API.
    :rtype: HostedZone
    :returns: An instantiated HostedZone object.
    """

    # This dict will be used to instantiate a HostedZone instance to yield.
    kwargs = {}
    # Within HostedZone tags are a number of sub-tags that include info
    # about the instance.
    for e_field in e_zone:
        # Cheesy way to strip off the namespace.
        tag_name = e_field.tag.split('}')[1]
        field_text = e_field.text

        if tag_name == 'Config':
            # Config has the Comment tag beneath it, needing
            # special handling.
            e_comment = e_field.find('./{*}Comment')
            kwargs['comment'] = e_comment.text if e_comment is not None else None
            continue
        elif tag_name == 'Id':
            # This comes back with a path prepended. Yank that sillyness.
            field_text = field_text.strip('/hostedzone/')

        # Map the XML tag name to a kwarg name.
        kw_name = HOSTED_ZONE_TAG_TO_KWARG_MAP[tag_name]
        # This will be the key/val pair used to instantiate the
        # HostedZone instance.
        kwargs[kw_name] = field_text

    return HostedZone(connection, **kwargs)

def parse_delegation_set(zone, e_delegation_set):
    """
    Parses a DelegationSet tag. These often accompany HostedZone tags in
    responses like CreateHostedZone and GetHostedZone.

    :param HostedZone zone: An existing HostedZone instance to populate.
    :param lxml.etree._Element e_delegation_set: A DelegationSet element.
    """

    e_nameservers = e_delegation_set.find('./{*}NameServers')

    nameservers = []
    for e_nameserver in e_nameservers:
        nameservers.append(e_nameserver.text)

    zone._nameservers = nameservers
