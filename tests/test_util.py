import unittest

from tests.test_basic import BaseTestCase

from datetime import timedelta, datetime, tzinfo
class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)

class UtilTestCase(BaseTestCase):
    """
    Tests utils
    """
        
    def test_parse_iso_8601_time_str(self):
        """
        At times, Amazon hands us a timestamp with no microseconds.
        """
        import datetime
        from route53.util import parse_iso_8601_time_str
        self.assertEqual(parse_iso_8601_time_str('2013-07-28T01:00:01Z'),
            datetime.datetime(2013, 7, 28, 1, 0, 1, 0, \
            tzinfo=UTC()))
        self.assertEqual(parse_iso_8601_time_str('2013-07-28T01:00:01.001Z'),
            datetime.datetime(2013, 7, 28, 1, 0, 1, 1000, \
            tzinfo=UTC()))
