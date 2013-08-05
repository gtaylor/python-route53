from lxml import etree
from route53 import xml_parsers, xml_generators
from route53.exceptions import Route53Error
from route53.transport import RequestsTransport
#from route53.util import prettyprint_xml
from route53.xml_parsers.common_change_info import parse_change_info

class Route53Connection(object):
    """
    Instances of this class are instantiated by the top-level
    :py:func:`route53.connect` function, and serve as a high level gateway
    to the Route 53 API. The majority of your interaction with these
    instances will probably be creating, deleting, and retrieving
    :py:class:`HostedZone <route53.hosted_zone.HostedZone>` instances.

    .. warning:: Do not instantiate instances of this class yourself.
    """

    endpoint_version = '2012-02-29'
    """The date-based API version. Mostly visible for your reference."""

    def __init__(self, aws_access_key_id, aws_secret_access_key):
        """
        :param str aws_access_key_id: An account's access key ID.
        :param str aws_secret_access_key: An account's secret access key.
        """

        self._endpoint = 'https://route53.amazonaws.com/%s/' % self.endpoint_version
        self._xml_namespace = 'https://route53.amazonaws.com/doc/%s/' % self.endpoint_version
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._transport = RequestsTransport(self)

    def _send_request(self, path, data, method):
        """
        Uses the HTTP transport to query the Route53 API. Runs the response
        through lxml's parser, before we hand it off for further picking
        apart by our call-specific parsers.

        :param str path: The RESTful path to tack on to the :py:attr:`endpoint`.
        :param data: The params to send along with the request.
        :type data: Either a dict or bytes, depending on the request type.
        :param str method: One of 'GET', 'POST', or 'DELETE'.
        :rtype: lxml.etree._Element
        :returns: An lxml Element root.
        """

        response_body = self._transport.send_request(path, data, method)
        root = etree.fromstring(response_body)
        #print(prettyprint_xml(root))
        return root

    def _do_autopaginating_api_call(self, path, params, method, parser_func,
        next_marker_xpath, next_marker_param_name,
        next_type_xpath=None, parser_kwargs=None):
        """
        Given an API method, the arguments passed to it, and a function to
        hand parsing off to, loop through the record sets in the API call
        until all records have been yielded.


        :param str method: The API method on the endpoint.
        :param dict params: The kwargs from the top-level API method.
        :param callable parser_func: A callable that is used for parsing the
            output from the API call.
        :param str next_marker_param_name: The XPath to the marker tag that
            will determine whether we continue paginating.
        :param str next_marker_param_name: The parameter name to manipulate
            in the request data to bring up the next page on the next
            request loop.
        :keyword str next_type_xpath: For the
            py:meth:`list_resource_record_sets_by_zone_id` method, there's
            an additional paginator token. Specifying this XPath looks for it.
        :keyword dict parser_kwargs: Optional dict of additional kwargs to pass
            on to the parser function.
        :rtype: generator
        :returns: Returns a generator that may be returned by the top-level
            API method.
        """

        if not parser_kwargs:
            parser_kwargs = {}

        # We loop indefinitely since we have no idea how many "pages" of
        # results we're going to have to go through.
        while True:
            # An lxml Element node.
            root = self._send_request(path, params, method)

            # Individually yield HostedZone instances after parsing/instantiating.
            for record in parser_func(root, connection=self, **parser_kwargs):
                yield record

            # This will determine at what offset we start the next query.
            next_marker = root.find(next_marker_xpath)
            if next_marker is None:
                # If the NextMarker tag is absent, we know we've hit the
                # last page.
                break

            # if NextMarker is present, we'll adjust our API request params
            # and query again for the next page.
            params[next_marker_param_name] = next_marker.text

            if next_type_xpath:
                # This is a _list_resource_record_sets_by_zone_id call. Look
                # for the given tag via XPath and adjust our type arg for
                # the next request. Without specifying this, we loop
                # infinitely.
                next_type = root.find(next_type_xpath)
                params['type'] = next_type.text

    def list_hosted_zones(self, page_chunks=100):
        """
        List all hosted zones associated with this connection's account. Since
        this method returns a generator, you can pull as many or as few
        entries as you'd like, without having to query and receive every
        hosted zone you may have.

        :keyword int page_chunks: This API call is "paginated" behind-the-scenes
            in order to break up large result sets. This number determines
            the maximum number of
            :py:class:`HostedZone <route53.hosted_zone.HostedZone>`
            instances to retrieve per request. The default is fine for almost
            everyone.

        :rtype: generator
        :returns: A generator of :py:class:`HostedZone <route53.hosted_zone.HostedZone>`
            instances.
        """

        return  self._do_autopaginating_api_call(
            path='hostedzone',
            params={'maxitems': page_chunks},
            method='GET',
            parser_func=xml_parsers.list_hosted_zones_parser,
            next_marker_xpath="./{*}NextMarker",
            next_marker_param_name="marker",
        )

    def create_hosted_zone(self, name, caller_reference=None, comment=None):
        """
        Creates and returns a new hosted zone. Once a hosted zone is created,
        its details can't be changed.

        :param str name: The name of the hosted zone to create.
        :keyword str caller_reference: A unique string that identifies the
            request and that allows failed create_hosted_zone requests to be
            retried without the risk of executing the operation twice. If no
            value is given, we'll generate a Type 4 UUID for you.
        :keyword str comment: An optional comment to attach to the zone.
        :rtype: tuple
        :returns: A tuple in the form of ``(hosted_zone, change_info)``.
            The ``hosted_zone`` variable contains a
            :py:class:`HostedZone <route53.hosted_zone.HostedZone>`
            instance matching the newly created zone, and ``change_info``
            is a dict with some details about the API request.
        """

        body = xml_generators.create_hosted_zone_writer(
            connection=self,
            name=name,
            caller_reference=caller_reference,
            comment=comment
        )

        root = self._send_request(
            path='hostedzone',
            data=body,
            method='POST',
        )

        return xml_parsers.created_hosted_zone_parser(
            root=root,
            connection=self
        )

    def get_hosted_zone_by_id(self, id):
        """
        Retrieves a hosted zone, by hosted zone ID (not name).

        :param str id: The hosted zone's ID (a short hash string).
        :rtype: :py:class:`HostedZone <route53.hosted_zone.HostedZone>`
        :returns: An :py:class:`HostedZone <route53.hosted_zone.HostedZone>`
            instance representing the requested hosted zone.
        """

        root = self._send_request(
            path='hostedzone/%s' % id,
            data={},
            method='GET',
        )

        return xml_parsers.get_hosted_zone_by_id_parser(
            root=root,
            connection=self,
        )

    def delete_hosted_zone_by_id(self, id):
        """
        Deletes a hosted zone, by hosted zone ID (not name).

        .. tip:: For most cases, we recommend deleting hosted zones via a
            :py:class:`HostedZone <route53.hosted_zone.HostedZone>`
            instance's
            :py:meth:`HostedZone.delete <route53.hosted_zone.HostedZone.delete>`
            method, but this saves an HTTP request if you already know the zone's ID.

        .. note:: Unlike
            :py:meth:`HostedZone.delete <route53.hosted_zone.HostedZone.delete>`,
            this method has no optional ``force`` kwarg.

        :param str id: The hosted zone's ID (a short hash string).
        :rtype: dict
        :returns: A dict of change info, which contains some details about
            the request.
        """

        root = self._send_request(
            path='hostedzone/%s' % id,
            data={},
            method='DELETE',
        )

        return xml_parsers.delete_hosted_zone_by_id_parser(
            root=root,
            connection=self,
        )

    def _list_resource_record_sets_by_zone_id(self, id, rrset_type=None,
                                             identifier=None, name=None,
                                             page_chunks=100):
        """
        Lists a hosted zone's resource record sets by Zone ID, if you
        already know it.

        .. tip:: For most cases, we recommend going through a
            :py:class:`HostedZone <route53.hosted_zone.HostedZone>`
            instance's
            :py:meth:`HostedZone.record_sets <route53.hosted_zone.HostedZone.record_sets>`
            property, but this saves an HTTP request if you already know the
            zone's ID.

        :param str id: The ID of the zone whose record sets we're listing.
        :keyword str rrset_type: The type of resource record set to begin the
            record listing from.
        :keyword str identifier: Weighted and latency resource record sets
            only: If results were truncated for a given DNS name and type,
            the value of SetIdentifier for the next resource record set
            that has the current DNS name and type.
        :keyword str name: Not really sure what this does.
        :keyword int page_chunks: This API call is paginated behind-the-scenes
            by this many ResourceRecordSet instances. The default should be
            fine for just about everybody, aside from those with tons of RRS.

        :rtype: generator
        :returns: A generator of ResourceRecordSet instances.
        """

        params = {
            'name': name,
            'type': rrset_type,
            'identifier': identifier,
            'maxitems': page_chunks,
        }

        return  self._do_autopaginating_api_call(
            path='hostedzone/%s/rrset' % id,
            params=params,
            method='GET',
            parser_func=xml_parsers.list_resource_record_sets_by_zone_id_parser,
            parser_kwargs={'zone_id': id},
            next_marker_xpath="./{*}NextRecordName",
            next_marker_param_name="name",
            next_type_xpath="./{*}NextRecordType"
        )

    def _change_resource_record_sets(self, change_set, comment=None):
        """
        Given a ChangeSet, POST it to the Route53 API.

        .. note:: You probably shouldn't be using this method directly,
            as there are convenience methods on the ResourceRecordSet
            sub-classes.

        :param change_set.ChangeSet change_set: The ChangeSet object to create
            the XML doc from.
        :keyword str comment: An optional comment to go along with the request.
        :rtype: dict
        :returns: A dict of change info, which contains some details about
            the request.
        """

        body = xml_generators.change_resource_record_set_writer(
            connection=self,
            change_set=change_set,
            comment=comment
        )

        root = self._send_request(
            path='hostedzone/%s/rrset' % change_set.hosted_zone_id,
            data=body,
            method='POST',
        )

        #print(prettyprint_xml(root))

        e_change_info = root.find('./{*}ChangeInfo')
        if e_change_info is None:
            error = root.find('./{*}Error').find('./{*}Message').text
            raise Route53Error(error)
        return parse_change_info(e_change_info)
