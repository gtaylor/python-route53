"""
Contains a parser for HostedZone tags. These are used in several kinds of
XML responses (ListHostedZones and CreateHostedZone, for example).
"""

from route53.hosted_zone import HostedZone

# This dict maps tag names in the API response to a kwarg key used to
# instantiate HostedZone instances.
from route53.util import parse_iso_8601_time_str

HOSTED_ZONE_TAG_TO_KWARG_MAP = {
    'Id': 'id',
    'Name': 'name',
    'CallerReference': 'caller_reference',
    'ResourceRecordSetCount': 'resource_record_set_count',
}

def parse_hosted_zone(zone, connection):
    """
    This a common parser that allows the passing of any valid HostedZone
    tag. It will spit out the appropriate HostedZone object for the tag.

    :param lxml.etree._Element zone: The root node of the etree parsed
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
    for field in zone:
        # Cheesy way to strip off the namespace.
        tag_name = field.tag.split('}')[1]
        field_text = field.text

        if tag_name == 'Config':
            # Config has the Comment tag beneath it, needing
            # special handling.
            comment = field.find('./{*}Comment')
            kwargs['comment'] = comment.text if comment is not None else None
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

def parse_change_info(e_change_info):
    """
    Parses a ChangeInfo tag. Seen in CreateHostedZone and DeleteHostedZone.

    :param lxml.etree._Element e_change_info: A ChangeInfo element.
    :rtype: dict
    :returns: A dict representation of the change info.
    """

    id = e_change_info.find('./{*}Id').text
    status = e_change_info.find('./{*}Status').text
    submitted_at = e_change_info.find('./{*}SubmittedAt').text
    submitted_at = parse_iso_8601_time_str(submitted_at)

    return {
        'request_id': id,
        'request_status': status,
        'request_submitted_at': submitted_at
    }