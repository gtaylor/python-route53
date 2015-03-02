"""
A few calls return a ChangeInfo tag with some details about the changes
that just happened.
"""

from route53.util import parse_iso_8601_time_str

def parse_change_info(e_change_info):
    """
    Parses a ChangeInfo tag. Seen in CreateHostedZone, DeleteHostedZone,
    and ChangeResourceRecordSetsRequest.

    :param lxml.etree._Element e_change_info: A ChangeInfo element.
    :rtype: dict
    :returns: A dict representation of the change info.
    """

    if e_change_info is None:
        return e_change_info

    status = e_change_info.find('./{*}Status').text
    submitted_at = e_change_info.find('./{*}SubmittedAt').text
    submitted_at = parse_iso_8601_time_str(submitted_at)

    return {
        'request_id': id,
        'request_status': status,
        'request_submitted_at': submitted_at
    }