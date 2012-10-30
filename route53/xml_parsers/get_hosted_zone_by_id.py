from route53.xml_parsers.common_hosted_zone import parse_hosted_zone, parse_delegation_set

def get_hosted_zone_by_id_parser(root, connection):
    """
    Parses the API responses for the
    :py:meth:`route53.connection.Route53Connection.get_hosted_zone_by_id` method.

    :param lxml.etree._Element root: The root node of the etree parsed
        response from the API.
    :param Route53Connection connection: The connection instance used to
        query the API.
    :rtype: HostedZone
    :returns: The requested HostedZone.
    """

    e_zone = root.find('./{*}HostedZone')
    # This pops out a HostedZone instance.
    hosted_zone =  parse_hosted_zone(e_zone, connection)
    # Now we'll fill in the nameservers.
    e_delegation_set = root.find('./{*}DelegationSet')
    # Modifies the HostedZone in place.
    parse_delegation_set(hosted_zone, e_delegation_set)
    return hosted_zone
