from route53.xml_parsers.common_hosted_zone import parse_hosted_zone

def created_hosted_zone_parser(root, connection):
    """
    Parses the API responses for the
    :py:meth:`route53.connection.Route53Connection.create_hosted_zone` method.

    :param lxml.etree._Element root: The root node of the etree parsed
        response from the API.
    :param Route53Connection connection: The connection instance used to
        query the API.
    :rtype: HostedZone
    :returns: The newly created HostedZone.
    """

    zone = root.find('./{*}HostedZone')
    return parse_hosted_zone(zone, connection)
