from route53.exceptions import RecordDoesNotExistError
from route53.transport import RequestsTransport
from route53 import parsers

class Route53Connection(object):
    """
    This class serves as the interface to the AWS Route53 API.
    """

    endpoint = 'https://route53.amazonaws.com/2012-02-29/'

    def __init__(self, aws_access_key_id, aws_secret_access_key):
        """
        :param str aws_access_key_id: An account's access key ID.
        :param str aws_secret_access_key: An account's secret access key.
        """

        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key

    def _send_request(self, path, params, method):
        return RequestsTransport(self).send_request(path, params, method)

    def _do_autopaginating_api_call(self, path, params, method, parser_func):
        """
        Given an API method, the arguments passed to it, and a function to
        hand parsing off to, loop through the record sets in the API call
        until all records have been yielded.

        This is mostly done this way to reduce duplication through the various
        API methods.

        :param str method: The API method on the endpoint.
        :param dict kwargs: The kwargs from the top-level API method.
        :param callable parser_func: A callable that is used for parsing the
            output from the API call.
        :rtype: generator
        :returns: Returns a generator that may be returned by the top-level
            API method.
        """
        # Used to determine whether to fail noisily if no results are returned.
        has_records = {"has_records": False}

        while True:
            try:
                root = self._send_request(path, params, method)
            except RecordDoesNotExistError:
                if not has_records["has_records"]:
                    # No records seen yet, this really is empty.
                    raise
                    # We've seen some records come through. We must have hit the
                # end of the result set. Finish up silently.
                return

            # This is used to track whether this go around the call->parse
            # loop yielded any records.
            records_returned_by_this_loop = False
            for record in parser_func(root, has_records):
                yield record
                # We saw a record, mark our tracker accordingly.
                records_returned_by_this_loop = True
                # There is a really fun bug in the Petfinder API with
            # shelter.getpets where an offset is returned with no pets,
            # causing an infinite loop.
            if not records_returned_by_this_loop:
                return

            # This will determine at what offset we start the next query.
            last_offset = root.find("lastOffset").text
            kwargs["offset"] = last_offset

    def list_hosted_zones(self):


        return parsers.list_hosted_zones_parser(
            self._send_request('hostedzone', {'maxitems': 2}, 'GET')
        )