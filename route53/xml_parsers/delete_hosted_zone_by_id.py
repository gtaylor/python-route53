from route53.xml_parsers.common_change_info import parse_change_info

#noinspection PyUnusedLocal
def delete_hosted_zone_by_id_parser(root, connection):
    """
    Parses the API responses for the
    :py:meth:`route53.connection.Route53Connection.delete_hosted_zone_by_id` method.

    :param lxml.etree._Element root: The root node of the etree parsed
        response from the API.
    :param Route53Connection connection: The connection instance used to
        query the API.
    :rtype: dict
    :returns: Details about the deletion.
    """

    e_change_info = root.find('./{*}ChangeInfo')

    return parse_change_info(e_change_info)
