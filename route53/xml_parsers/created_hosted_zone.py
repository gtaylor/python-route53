from route53.xml_parsers.common_change_info import parse_change_info
from route53.xml_parsers.common_hosted_zone import parse_hosted_zone, parse_delegation_set

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
    # This pops out a HostedZone instance.
    hosted_zone = parse_hosted_zone(zone, connection)

    # Now we'll fill in the nameservers.
    e_delegation_set = root.find('./{*}DelegationSet')
    # Modifies the HostedZone in place.
    parse_delegation_set(hosted_zone, e_delegation_set)

    # With each CreateHostedZone request, there's some details about the
    # request's ID, status, and submission time. We'll return this in a tuple
    # just for the sake of completeness.
    e_change_info = root.find('./{*}ChangeInfo')
    # Translate the ChangeInfo values to a dict.
    change_info = parse_change_info(e_change_info)

    return hosted_zone, change_info