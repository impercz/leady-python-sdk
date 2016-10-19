from __future__ import print_function, unicode_literals

try:
    from urllib.parse import urlencode, quote
    from http.client import HTTPSConnection, HTTPException
    PY2 = False
except ImportError:
    from urllib import urlencode, quote
    from httplib import HTTPSConnection, HTTPException
    PY2 = True

import logging
import re
import uuid


log = logging.getLogger('leady')

TRACK_URL = 't.leady.cz'


class LeadyTrackerError(Exception):
    pass


class LeadyTracker(object):

    def __init__(self, track_key, identifier):
        self._identifier = identifier
        self._track_key = track_key
        self._params = dict(k=track_key)
        self._email = None
        self._events = []
        self._conn = HTTPSConnection(TRACK_URL)

    def identify(self, email, user_agent='', ip_address='', url=''):
        self._email = email
        if url:
            if PY2:
                url = unicode(bytes(url), 'utf-8')
            url = quote(url.encode('utf-8'), safe=b"/:@&+$,-_.!~*'()?=#")
            url = re.sub(r'#.+$', '', url)
        self._params.update(dict(b=user_agent, p=ip_address, l=url))

    def track(self, event_name, event_category, event_value=None, push=True):
        event = [event_name, event_category]
        if event_value:
            event.append(event_value)
        self._events.append(event)
        if push:
            self.push()

    def push(self):
        if not self._email:
            raise LeadyTrackerError('You must call identify() before tracking events')

        self._events.append(['identify', self._email])
        self._conn.request('GET', '/L?%s' % urlencode(dict(e=self._events).update(self._params)))
        resp = self._conn.getresponse()
        if resp.status == 204:
            # clear events
            self._events = []
        else:
            log.warning('Response status code: %s' % resp.status)


class DjangoLeadyTracker(LeadyTracker):
    _cookie_name = 'django_leady_tracker'

    def __init__(self, track_key, request):
        super(DjangoLeadyTracker, self).__init__(track_key, request.META['HTTP_HOST'])
        self.request = request
        self._cookie_value = request.COOKIES.get(self._cookie_name, str(uuid.uuid4()))
        self._params.update(dict(
            b=request.META['HTTP_USER_AGENT'],
            l=request.get_full_path(),
            p=self.client_ip,
            s=self._cookie_value
        ))

    def identify(self, email, user_agent='', ip_address='', url=''):
        # only set email, do not update params which are obtained from request
        self._email = email

    def track(self, event_name, event_category, event_value=None, push=False):
        super(DjangoLeadyTracker, self).track(event_name, event_category, event_value, push)

    def set_cookie(self, response):
        response.set_cookie(self._cookie_name, self._cookie_value, 60*60*24*365*2)

    @property
    def js_code(self):
        from django.utils.safestring import mark_safe
        evts = ['_leady.push(%s);' % ['identify', self._email]]
        for one in self._events:
            one.insert(0, 'event')
            evts.append('_leady.push(%s);' % one)
        return mark_safe("""<script type="text/javascript">
var _leady = _leady || [];
%s
</script>""") % '\n'.join(evts)

    @property
    def client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else self.request.META.get('REMOTE_ADDR')
