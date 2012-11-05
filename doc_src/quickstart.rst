.. _quickstart:

.. include:: global.txt

Quickstart
==========

This section goes over how to get up and running quickly. We'll assume that
you have already followed the :doc:`installation` instructions, and are
ready to go.

AWS credentials
---------------

Before you can make your first query to `Route 53`_, you'll need obtain your
API credentials. Visit your `security credentials`_ page and note your
*Access Key ID* and *Secret Access Key*.

.. _security credentials: https://portal.aws.amazon.com/gp/aws/securityCredentials

Instantiate the API client
--------------------------

Next, you'll want to import the module::

    import route53

You can then instantiate a connection to Route53::

    conn = route53.connect(
        aws_access_key_id='YOURACCESSKEYHERE',
        aws_secret_access_key='YOURSECRETACCESSKEYHERE',
    )

You are now ready to roll.

Listing Hosted Zones
--------------------

The :py:meth:`list_hosted_zones` method returns a generator of
:py:class:`HostedZone` instances::

    # This is a generator.
    for zone in conn.list_hosted_zones():
        print(zone.name)

Creating a Hosted Zone
----------------------

The :py:meth:`create_hosted_zone` method creates Hosted Zones::

    new_zone, change_info = conn.create_hosted_zone(
        'some-domain.com.', comment='An optional comment.'
    )
    # You can then manipulate the HostedZone.
    print("Zone ID", new_zone.id)

In this case, ``new_zone`` is a new :py:class:`HostedZone` instance, and
``change_info`` is a dict with some details about the changes pending (from
the Route 53 API).

Retrieving a Hosted Zone
------------------------

The :py:meth:`get_hosted_zone_by_id` method retrieves a specific Hosted Zone,
by Zone ID::

    zone = conn.get_hosted_zone_by_id('ZONE-ID-HERE')

Deleting a Hosted Zone
----------------------

Simply call the :py:meth:`delete` method on a :py:class:`HostedZone` to delete
it::

    zone = conn.get_hosted_zone_by_id('ZONE-ID-HERE')
    zone.delete()

If you have record sets under the hosted zone, you'll need to delete those
first, or an exception will be raised. Alternatively, you can
call :py:meth:`delete` with ``force=True`` to delete the record sets and the
hosted zones::

    zone.delete(force=True)

Creating a record set
---------------------

Depending on which kind of record set you'd like to create, choose the
appropriate ``create_*_record`` method on :py:class:`HostedZone`. The methods
return one of the :py:class:`ResourceRecordSet` sub-classes::

    new_record, change_info = zone.create_a_record(
        # Notice that this is a full-qualified name.
        name='test.some-domain.com.',
        # A list of IP address entries, in the case fo an A record.
        values=['8.8.8.8'],
    )

Listing record sets
-------------------

In order to list record sets, use the ``record_sets`` property on
:py:class:`HostedZone`. Note that we don't currently implement any convenience
methods for finding record sets, so this is the way to go::

    for record_set in zone.record_sets:
        print(record_set)

Changing a record set
---------------------

Simply change one of the attributes on the :py:class:`ResourceRecordSet`
instance and call its :py:meth:`save` method::

    record_set.values = ['8.8.8.7']
    record_set.save()

Deleting a record set
---------------------

Similarly, delete a record set via its :py:meth:`delete` method::

    record_set.delete()

