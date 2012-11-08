.. _quickstart:

.. include:: global.txt

Quickstart
==========

This section goes over how to get up and running quickly. We'll assume that
you have already followed the :doc:`installation` instructions, and are
ready to go.

.. tip:: It's best to combine our documentation with the
    `Route 53 Documentation`_. While we'll do our best to make this as
    simple as possible, it may be necessary to look at what they've got for
    more details on behavior and how things work.

AWS credentials
---------------

Before you can make your first query to `Route 53`_, you'll need obtain your
API credentials. Visit your `security credentials`_ page and note your
*Access Key ID* and *Secret Access Key*.

.. _security credentials: https://portal.aws.amazon.com/gp/aws/securityCredentials

Instantiate the API client
--------------------------

Next, you'll want to import the module:

.. code-block:: python

    import route53

You can then instantiate a connection to Route53 via :py:func:`route53.connect`:

.. code-block:: python

    conn = route53.connect(
        aws_access_key_id='YOURACCESSKEYHERE',
        aws_secret_access_key='YOURSECRETACCESSKEYHERE',
    )

You are now ready to roll. Continue reading to see how much fun there is
to be had (hooray!).

Listing Hosted Zones
--------------------

Let's say you want to retrieve a representation of all of your currently
existing hosted zones. These roughly correspond to domains, ala
angry-squirrel.com, or python.org.

The :py:meth:`Route53Connection.list_hosted_zones <route53.connection.Route53Connection.list_hosted_zones>`
method returns a generator of
:py:class:`HostedZone <route53.hosted_zone.HostedZone>` instances:

.. code-block:: python

    # This is a generator.
    for zone in conn.list_hosted_zones():
        # You can then do various things to the zone.
        print(zone.name)

        # Perhaps you want to see the record sets under this zone
        for record_set in zone.record_sets:
            print(record_set)

        # Or maybe you don't like this zone, and want to blow it away.
        zone.delete()

Creating a Hosted Zone
----------------------

The :py:meth:`Route53Connection.create_hosted_zone <route53.connection.Route53Connection.create_hosted_zone>`
method creates hosted zones, and returns a tuple that contains a
:py:class:`HostedZone <route53.hosted_zone.HostedZone>`
instance, and some details about the pending change from the API:

.. code-block:: python

    new_zone, change_info = conn.create_hosted_zone(
        'some-domain.com.', comment='An optional comment.'
    )

    # You can then manipulate the HostedZone.
    print("Zone ID", new_zone.id)

    # This has some details about the change from the API.
    print(change_info)

.. note:: Notice that we passed in a fully-qualified domain name,
    ``some-domain.com.``, ending in a period.

In this case, ``new_zone`` is a new :py:class:`HostedZone <route53.hosted_zone.HostedZone>`
instance, and ``change_info`` is a dict with some details about the changes
pending (from the Route 53 API).

Retrieving a Hosted Zone
------------------------

The
:py:meth:`Route53Connection.get_hosted_zone_by_id <route53.connection.Route53Connection.get_hosted_zone_by_id>`
method retrieves a specific hosted zone, by Zone ID:

.. code-block:: python

    zone = conn.get_hosted_zone_by_id('ZONE-ID-HERE')

.. note:: A Zone ID is not the same thing as the domain name. The Zone ID
    is a unique string identifier for the hosted zone, as per Route 53's
    records.

Deleting a Hosted Zone
----------------------

Simply call the :py:meth:`HostedZone.delete <route53.hosted_zone.HostedZone.delete>`
method on a :py:class:`HostedZone <route53.hosted_zone.HostedZone>` to delete
it:

.. code-block:: python

    zone = conn.get_hosted_zone_by_id('ZONE-ID-HERE')
    zone.delete()

If you have record sets under the hosted zone, you'll need to delete those
first, or an exception will be raised. Alternatively, you can
call :py:meth:`delete` with ``force=True`` to delete the record sets and the
hosted zones:

.. code-block:: python

    zone.delete(force=True)

Creating a record set
---------------------

Depending on which kind of record set you'd like to create, choose the
appropriate ``create_*_record`` method on
:py:class:`HostedZone <route53.hosted_zone.HostedZone>`. The methods
return one of the :py:class:`ResourceRecordSet` sub-classes:

.. code-block:: python

    new_record, change_info = zone.create_a_record(
        # Notice that this is a full-qualified name.
        name='test.some-domain.com.',
        # A list of IP address entries, in the case fo an A record.
        values=['8.8.8.8'],
    )

    # Or maybe we want a weighted round-robin set.
    wrr_record1, change_info = zone.create_a_record(
        name='wrrtest.some-domain.com.',
        values=['8.8.8.8'],
        weight=1
        set_identifier='set123,
    )
    wrr_record2, change_info = zone.create_a_record(
        name='wrrtest.some-domain.com.',
        values=['6.6.6.6'],
        weight=2
        set_identifier='set123,
    )

Listing record sets
-------------------

In order to list record sets, use the
:py:meth:`HostedZone.record_sets <route53.hosted_zone.HostedZone.record_sets>`
property on :py:class:`HostedZone <route53.hosted_zone.HostedZone>`.
Note that we don't currently implement any convenience
methods for finding record sets, so this is the way to go:

.. code-block:: python

    # Note that this is a fully-qualified domain name.
    name_to_match = 'fuzzy.bunny.com.'
    for record_set in zone.record_sets:
        if record_set.name == name_to_match:
            print(record_set)
            # Stopping early may save some additional HTTP requests,
            # since zone.record_sets is a generator.
            break

While it may seem like extra work to craft these filters yourself, it does
prevent needless additional iteration, and keeps the API more concise.

Changing a record set
---------------------

Simply change one of the attributes on the various :py:class:`ResourceRecordSet`
sub-classed instances and call its :py:meth:`save` method:

.. code-block:: python

    record_set.values = ['8.8.8.7']
    record_set.save()

Deleting a record set
---------------------

Similarly, delete a record set via its :py:meth:`delete` method:

.. code-block:: python

    record_set.delete()

