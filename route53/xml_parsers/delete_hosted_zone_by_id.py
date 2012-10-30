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

    id = e_change_info.find('./{*}Id').text
    status = e_change_info.find('./{*}Status').text
    submitted_at = e_change_info.find('./{*}SubmittedAt').text

    return {
        'request_id': id,
        'request_status': status,
        'request_submitted_at': submitted_at
    }
