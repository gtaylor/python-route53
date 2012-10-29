from route53.hosted_zone import HostedZone

# This dict maps tag names in the API response to a kwarg key used to
# instantiate HostedZone instances.
HOSTED_ZONE_TAG_TO_KWARG_MAP = {
    'Id': 'id',
    'Name': 'name',
    'CallerReference': 'caller_reference',
    'ResourceRecordSetCount': 'resource_record_set_count',
}

def list_hosted_zones_parser(root, connection):
    """
    Parses the API responses for the
    :py:meth:`route53.connection.Route53Connection.list_hosted_zones` method.

    :param lxml.etree._Element root: The root node of the etree parsed
        response from the API.
    :param Route53Connection connection: The connection instance used to
        query the API.
    :rtype: HostedZone
    :returns: A generator of fully formed HostedZone instances.
    """

    # The rest of the list pagination tags are handled higher up in the stack.
    # We'll just worry about the HostedZones tag, which has HostedZone tags
    # nested beneath it.
    zones = root.find('./{*}HostedZones')

    for zone in zones:
        # This dict will be used to instantiate a HostedZone instance to yield.
        kwargs = {}
        # Within HostedZone tags are a number of sub-tags that include info
        # about the instance.
        for field in zone:
            # Cheesy way to strip off the namespace.
            tag_name = field.tag.split('}')[1]

            if tag_name == 'Config':
                # Config has the Comment tag beneath it, needing
                # special handling.
                comment = field.find('./{*}Comment')
                kwargs['comment'] = comment.text if comment is not None else None
                continue

            # Map the XML tag name to a kwarg name.
            kw_name = HOSTED_ZONE_TAG_TO_KWARG_MAP[tag_name]
            # This will be the key/val pair used to instantiate the
            # HostedZone instance.
            kwargs[kw_name] = field.text

        yield HostedZone(connection, **kwargs)
