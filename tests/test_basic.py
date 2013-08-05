import unittest
import route53
from route53.exceptions import AlreadyDeletedError
from route53.transport import BaseTransport
from tests.utils import get_route53_connection

class BaseTestCase(unittest.TestCase):
    """
    A base unit test class that has some generally useful stuff for the
    various test cases.
    """

    test_zone_name = 'route53-unittest-zone.com.'

    def setUp(self):
        self.conn = get_route53_connection()

    def tearDown(self):
        for zone in self.conn.list_hosted_zones():
            if zone.name == self.test_zone_name:
                zone.delete(force=True)


class BaseTransportTestCase(unittest.TestCase):
    """
    Tests for the various HTTP transports.
    """

    def test_hmac_signing(self):
        """
        Makes sure our HMAC signing methods are matching expected output
        for a pre-determined key/value.
        """

        conn = route53.connect(
            aws_access_key_id='BLAHBLAH',
            aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        )
        trans = BaseTransport(conn)
        signed = trans._hmac_sign_string('Thu, 14 Aug 2008 17:08:48 GMT')
        self.assertEquals(signed, 'PjAJ6buiV6l4WyzmmuwtKE59NJXVg5Dr3Sn4PCMZ0Yk=')


class HostedZoneTestCase(BaseTestCase):
    """
    Tests for manipulating hosted zones.
    """

    def test_sequence(self):
        """
        Runs through a sequence of calls to test hosted zones.
        """

        # Create a new hosted zone.
        new_zone, change_info = self.conn.create_hosted_zone(
            self.test_zone_name, comment='A comment here.'
        )
        # Make sure the change info came through.
        self.assertIsInstance(change_info, dict)

        # Now get a list of all zones. Look for the one we just created.
        found_match = False
        for zone in self.conn.list_hosted_zones():
            if zone.name == new_zone.name:
                found_match = True

                # ListHostedZones doesn't return nameservers.
                # We lazy load them in this case. Initially, the nameservers
                # are empty.
                self.assertEqual(zone._nameservers, [])
                # This should return the nameservers
                self.assertNotEqual(zone.nameservers, [])
                # This should now be populated.
                self.assertNotEqual(zone._nameservers, [])

                break
        # If a match wasn't found, we're not happy.
        self.assertTrue(found_match)

        # Now attempt to retrieve the newly created HostedZone.
        zone = self.conn.get_hosted_zone_by_id(new_zone.id)
        # Its nameservers should be populated.
        self.assertNotEqual([], zone.nameservers)

        zone.delete()
        # Trying to delete a second time raises an exception.
        self.assertRaises(AlreadyDeletedError, zone.delete)
        # Attempting to add a record set to an already deleted zone does the same.
        self.assertRaises(AlreadyDeletedError,
            zone.create_a_record,
                'test.' + self.test_zone_name,
                ['8.8.8.8']
        )


class ResourceRecordSetTestCase(BaseTestCase):
    """
    Tests related to RRSets. Deletions are tested in the cleanUp() method,
    on the base class, more or less.
    """

    def test_create_rrset(self):
        """
        Tests creation of various record sets.
        """

        new_zone, change_info = self.conn.create_hosted_zone(
            'route53-unittest-zone.com.'
        )
        self.assertIsInstance(change_info, dict)

        new_record, change_info = new_zone.create_a_record(
            name='test.route53-unittest-zone.com.',
            values=['8.8.8.8'],
        )
        self.assertIsInstance(change_info, dict)

        # Initial values should equal current values.
        for key, val in new_record._initial_vals.items():
            self.assertEqual(getattr(new_record, key), val)

    def test_change_existing_rrset(self):
        """
        Tests changing an existing record set.
        """

        new_zone, change_info = self.conn.create_hosted_zone(
            'route53-unittest-zone.com.'
        )
        self.assertIsInstance(change_info, dict)

        new_record, change_info = new_zone.create_a_record(
            name='test.route53-unittest-zone.com.',
            values=['8.8.8.8'],
        )
        self.assertIsInstance(change_info, dict)

        new_record.values = ['8.8.8.7']
        new_record.save()

        # Initial values should equal current values after the save.
        for key, val in new_record._initial_vals.items():
            self.assertEqual(getattr(new_record, key), val)
