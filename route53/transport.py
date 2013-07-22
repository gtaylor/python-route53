"""
This module contains HTTP transports used for communicating with the
Route53 API endpoint.
"""

import time
import base64
import hmac
import hashlib
import requests
from route53.exceptions import Route53Error

class BaseTransport(object):
    """
    This serves as an interface for HTTP transports. It provides a really
    simple blueprint for what is involved in working with the Route53
    API.
    """

    def __init__(self, connection):
        """
        :param Route53Connection connection: The connection being used with
            the transport. The connection contains their AWS credentials
            and a few other settings.
        """

        self.connection = connection

    @property
    def endpoint(self):
        """
        :rtype: str
        :returns: The Route53 API endpoint to query against.
        """

        return self.connection._endpoint

    def _hmac_sign_string(self, string_to_sign):
        """
        Route53 uses AWS an HMAC-based authentication scheme, involving the
        signing of a date string with the user's secret access key. More details
        on the specifics can be found in their documentation_.

        .. documentation:: http://docs.amazonwebservices.com/Route53/latest/DeveloperGuide/RESTAuthentication.html

        This method is used to sign said time string, for use in the request
        headers.


        :param str string_to_sign: The time string to sign.
        :rtype: str
        :returns: An HMAC signed string.
        """

        # Just use SHA256, since we're all running modern versions
        # of Python (right?).
        new_hmac = hmac.new(
            self.connection._aws_secret_access_key.encode('utf-8'),
            digestmod=hashlib.sha256
        )
        new_hmac.update(string_to_sign.encode('utf-8'))
        # The HMAC digest str is done at this point.
        digest = new_hmac.digest()
        # Now we have to Base64 encode it, and we're done.
        return base64.b64encode(digest).decode('utf-8')

    def get_request_headers(self):
        """
        Determine the headers to send along with the request. These are
        pretty much the same for every request, with Route53.
        """

        date_header = time.asctime(time.gmtime())
        # We sign the time string above with the user's AWS secret access key
        # in order to authenticate our request.
        signing_key = self._hmac_sign_string(date_header)

        # Amazon's super fun auth token.
        auth_header = "AWS3-HTTPS AWSAccessKeyId=%s,Algorithm=HmacSHA256,Signature=%s" % (
            self.connection._aws_access_key_id,
            signing_key,
        )

        return {
            'X-Amzn-Authorization': auth_header,
            'x-amz-date': date_header,
            'Host': 'route53.amazonaws.com',
        }

    def send_request(self, path, data, method):
        """
        All outbound requests go through this method. It defers to the
        transport's various HTTP method-specific methods.

        :param str path: The path to tack on to the endpoint URL for
            the query.
        :param data: The params to send along with the request.
        :type data: Either a dict or bytes, depending on the request type.
        :param str method: One of 'GET', 'POST', or 'DELETE'.

        :rtype: str
        :returns: The body of the response.
        """

        headers = self.get_request_headers()

        if method == 'GET':
            return self._send_get_request(path, data, headers)
        elif method == 'POST':
            return self._send_post_request(path, data, headers)
        elif method == 'DELETE':
            return self._send_delete_request(path, headers)
        else:
            raise Route53Error("Invalid request method: %s" % method)

    def _send_get_request(self, path, params, headers):
        """
        Transport sub-classes need to override this.

        Sends the GET request to the Route53 endpoint.

        :param str path: The path to tack on to the endpoint URL for
            the query.
        :param dict params: Key/value pairs to send.
        :param dict headers: A dict of headers to send with the request.
        :rtype: str
        :returns: The body of the response.
        """

        raise NotImplementedError

    def _send_post_request(self, path, data, headers):
        """
        Transport sub-classes need to override this.

        Sends the POST request to the Route53 endpoint.

        :param str path: The path to tack on to the endpoint URL for
            the query.
        :param data: Either a dict, or bytes.
        :type data: dict or bytes
        :param dict headers: A dict of headers to send with the request.
        :rtype: str
        :returns: The body of the response.
        """

        raise NotImplementedError

    def _send_delete_request(self, path, headers):
        """
        Transport sub-classes need to override this.

        Sends the DELETE request to the Route53 endpoint.

        :param str path: The path to tack on to the endpoint URL for
            the query.
        :param dict headers: A dict of headers to send with the request.
        :rtype: str
        :returns: The body of the response.
        """

        raise NotImplementedError


class RequestsTransport(BaseTransport):
    """
    A requests-based transport. More details may be found on the
    `requests webpage`_.

    .. _requests webpage: http://docs.python-requests.org/en/latest/
    """

    def _send_get_request(self, path, params, headers):
        """
        Sends the GET request to the Route53 endpoint.

        :param str path: The path to tack on to the endpoint URL for
            the query.
        :param dict params: Key/value pairs to send.
        :param dict headers: A dict of headers to send with the request.
        :rtype: str
        :returns: The body of the response.
        """

        r = requests.get(self.endpoint + path, params=params, headers=headers)
        r.raise_for_status()
        return r.text

    def _send_post_request(self, path, data, headers):
        """
        Sends the POST request to the Route53 endpoint.

        :param str path: The path to tack on to the endpoint URL for
            the query.
        :param data: Either a dict, or bytes.
        :type data: dict or bytes
        :param dict headers: A dict of headers to send with the request.
        :rtype: str
        :returns: The body of the response.
        """

        r = requests.post(self.endpoint + path, data=data, headers=headers)
        return r.text

    def _send_delete_request(self, path, headers):
        """
        Sends the DELETE request to the Route53 endpoint.

        :param str path: The path to tack on to the endpoint URL for
            the query.
        :param dict headers: A dict of headers to send with the request.
        :rtype: str
        :returns: The body of the response.
        """

        r = requests.delete(self.endpoint + path, headers=headers)
        return r.text
