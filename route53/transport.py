import time
import base64
import hmac
import hashlib
import requests

def formatdate(timeval=None, localtime=False, usegmt=False):
    """Returns a date string as specified by RFC 2822, e.g.:

    Fri, 09 Nov 2001 01:08:47 -0000

    Optional timeval if given is a floating point time value as accepted by
    gmtime() and localtime(), otherwise the current time is used.

    Optional localtime is a flag that when True, interprets timeval, and
    returns a date relative to the local timezone instead of UTC, properly
    taking daylight savings time into account.

    Optional argument usegmt means that the timezone is written out as
    an ascii string, not numeric one (so "GMT" instead of "+0000"). This
    is needed for HTTP, and is only used when localtime==False.
    """

    # Note: we cannot use strftime() because that honors the locale and RFC
    # 2822 requires that day and month names be the English abbreviations.
    if timeval is None:
        timeval = time.time()
    if localtime:
        now = time.localtime(timeval)
        # Calculate timezone offset, based on whether the local zone has
        # daylight savings time, and whether DST is in effect.
        if time.daylight and now[-1]:
            offset = time.altzone
        else:
            offset = time.timezone
        hours, minutes = divmod(abs(offset), 3600)
        # Remember offset is in seconds west of UTC, but the timezone is in
        # minutes east of UTC, so the signs differ.
        if offset > 0:
            sign = '-'
        else:
            sign = '+'
        zone = '%s%02d%02d' % (sign, hours, minutes // 60)
    else:
        now = time.gmtime(timeval)
        # Timezone offset is always -0000
        if usegmt:
            zone = 'GMT'
        else:
            zone = '-0000'
    return '%s, %02d %s %04d %02d:%02d:%02d %s' % (
        ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][now[6]],
        now[2],
        ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][now[1] - 1],
        now[0], now[3], now[4], now[5],
        zone)

class BaseTransport(object):
    def __init__(self, connection):
        self.connection = connection

    @property
    def endpoint(self):
        return self.connection.endpoint

    def _hmac_sign_string(self, string_to_sign):
        new_hmac = hmac.new(
            self.connection.aws_secret_access_key.encode('utf-8'),
            digestmod=hashlib.sha256
        )
        new_hmac.update(string_to_sign.encode('utf-8'))
        digest = new_hmac.digest()
        return base64.b64encode(digest).decode('utf-8')

    def get_request_headers(self):
        date_header = time.asctime(time.gmtime())
        signing_key = self._hmac_sign_string(date_header)

        auth_header = "AWS3-HTTPS AWSAccessKeyId=%s,Algorithm=HmacSHA256,Signature=%s" % (
            self.connection.aws_access_key_id,
            signing_key,
        )

        headers = {
            'X-Amzn-Authorization': auth_header,
            'x-amz-date': date_header,
            'Host': 'route53.amazonaws.com',
        }
        return headers

    def send_request(self, path, params, method):
        headers = self.get_request_headers()

        if method == 'GET':
            return self._send_get_request(path, params, headers)
        elif method == 'POST':
            return self._send_post_request(path, params, headers)
        else:
            raise Exception("Invalid request method: %s" % method)

    def _send_get_request(self, path, params, headers):
        raise NotImplementedError

    def _send_post_request(self, path, params, headers):
        raise NotImplementedError

class RequestsTransport(BaseTransport):

    def _send_get_request(self, path, params, headers):
        r = requests.get(self.endpoint + path, params=params, headers=headers)
        return r.text

    def _send_post_request(self, path, params, headers):
        r = requests.post(self.endpoint + path, params=params, headers=headers)
        return r.text