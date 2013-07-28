"""
Various utility stuff that is useful across the codebase.
"""

import datetime
import re

import pytz
from lxml import etree

# This can be used as a tzinfo arg to the datetime functions/methods.
UTC_TIMEZONE = pytz.utc

def parse_iso_8601_time_str(time_str):
    """
    Parses a standard ISO 8601 time string. The Route53 API uses these here
    and there.

    :param str time_str: An ISO 8601 time string.
    :rtype: datetime.datetime
    :returns: A timezone aware (UTC) datetime.datetime instance.
    """
    if re.search('\.\d{3}Z$', time_str):
        submitted_at = datetime.datetime.strptime(time_str, \
            '%Y-%m-%dT%H:%M:%S.%fZ')
    else:
        submitted_at = datetime.datetime.strptime(time_str, \
            '%Y-%m-%dT%H:%M:%SZ')
    # Parse the string, and make it explicitly UTC.
    return submitted_at.replace(tzinfo=UTC_TIMEZONE)

def prettyprint_xml(element):
    """
    A rough and dirty way to prettyprint an Element with indention.

    :param lxml.etree._Element element: The Element or ElementTree to format.
    :rtype: str
    :returns: A prettyprinted representation of the element.
    """

    return etree.tostring(element, pretty_print=True).decode('utf-8')
