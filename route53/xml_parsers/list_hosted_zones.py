from route53.xml_parsers.common_hosted_zone import parse_hosted_zone

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
        yield parse_hosted_zone(zone, connection)
