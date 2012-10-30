from lxml import etree
from route53 import xml_parsers, xml_generators
from route53.transport import RequestsTransport
from route53.util import prettyprint_xml

class Route53Connection(object):
    """
    This class serves as the interface to the AWS Route53 API.
    """

    endpoint_version = '2012-02-29'

    def __init__(self, aws_access_key_id, aws_secret_access_key):
        """
        :param str aws_access_key_id: An account's access key ID.
        :param str aws_secret_access_key: An account's secret access key.
        """

        self.endpoint = 'https://route53.amazonaws.com/%s/' % self.endpoint_version
        self.xml_namespace = 'https://route53.amazonaws.com/doc/%s/' % self.endpoint_version
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.transport = RequestsTransport(self)

    def _send_request(self, path, params, method):
        """
        Uses the HTTP transport to query the Route53 API. Runs the response
        through lxml's parser, before we hand it off for further picking
        apart by our call-specific parsers.

        :param str path: The RESTful path to tack on to the :py:attr:`endpoint`.
        :param dict params: A dict of GET or POST params.
        :param str method: One of 'GET', 'POST', or 'DELETE'.
        :rtype: lxml.etree._Element
        :returns: An lxml Element root.
        """

        response_body = self.transport.send_request(path, params, method)
        root = etree.fromstring(response_body)
        print(prettyprint_xml(root))
        return root

    def _do_autopaginating_api_call(self, path, params, method, parser_func):
        """
        Given an API method, the arguments passed to it, and a function to
        hand parsing off to, loop through the record sets in the API call
        until all records have been yielded.


        :param str method: The API method on the endpoint.
        :param dict params: The kwargs from the top-level API method.
        :param callable parser_func: A callable that is used for parsing the
            output from the API call.
        :rtype: generator
        :returns: Returns a generator that may be returned by the top-level
            API method.
        """

        # We loop indefinitely since we have no idea how many "pages" of
        # results we're going to have to go through.
        while True:
            # An lxml Element node.
            root = self._send_request(path, params, method)

            # Individually yield HostedZone instances after parsing/instantiating.
            for record in parser_func(root, connection=self):
                yield record

            # This will determine at what offset we start the next query.
            next_marker = root.find("./{*}NextMarker")
            if next_marker is None:
                # If the NextMarker tag is absent, we know we've hit the
                # last page.
                break

            # if NextMarker is present, we'll adjust our API request params
            # and query again for the next page.
            params["marker"] = next_marker.text

    def list_hosted_zones(self, page_chunks=100):
        """
        List all hosted zones associated with this connection's account. Since
        this method returns a generator, you can pull as many or as few
        entries as you'd like, without having to query and receive every
        hosted zone you may have.

        :keyword int page_chunks: This API call is paginated behind-the-scenes
            by this many HostedZone instances. The default should be fine for
            just about everybody, aside from those with tons of zones.

        :rtype: generator
        :returns: A generator of HostedZone instances.
        """

        return  self._do_autopaginating_api_call(
            path='hostedzone',
            params={'maxitems': page_chunks},
            method='GET',
            parser_func=xml_parsers.list_hosted_zones_parser,
        )

    def create_hosted_zone(self, name, caller_reference=None, comment=None):
        """
        Creates a new hosted zone.
        """

        body = xml_generators.create_hosted_zone_writer(
            connection=self,
            name=name,
            caller_reference=caller_reference,
            comment=comment
        )

        root = self._send_request(
            path='hostedzone',
            params=body,
            method='POST',
        )

        return xml_parsers.created_hosted_zone_parser(
            root=root,
            connection=self
        )
