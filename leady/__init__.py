from __future__ import print_function, unicode_literals

import json
import re
import uuid
from collections import OrderedDict
from random import randint

try:
    from urllib.parse import urlencode, quote_plus
    from http.client import HTTPSConnection, HTTPException
    PY2 = False
except ImportError:
    from urllib import urlencode, quote_plus
    from httplib import HTTPSConnection, HTTPException
    PY2 = True


class LeadyTrackerError(Exception):
    pass


class LeadyTracker(object):

    TRACK_URL = 't.leady.cz'
    SUPPORTED_PARAM_KEYS = 'kdslrbuoe'
    DIR_ALLOWED = 'ioe'
    DIR_I, DIR_O, DIR_E = DIR_ALLOWED

    def __init__(self, track_key, auto_referrer=True, session=uuid.uuid4(), base_location='', user_agent=''):
        track_key = str(track_key)
        assert len(track_key) == 16, "Invalid track_key parameter"
        assert len(user_agent) < 256, "Too long user_agent parameter"
        assert len(base_location) < 156, "Too long base_url parameter"

        if session and not isinstance(session, uuid.UUID):
            try:
                session = uuid.UUID(session)
            except ValueError:
                raise LeadyTrackerError('Invalid session parameter, expected UUID str, got %s: %s' % (type(session), session))

        self.session = str(session)
        self.track_key = track_key
        self.auto_referrer = auto_referrer
        self.base_location = base_location
        self.headers = {'User-agent': user_agent} if user_agent else {}
        self.last_location = ''
        self.events_to_push = []

    def make_params(self):
        params = OrderedDict(((k, '') for k in self.SUPPORTED_PARAM_KEYS))
        params.update(k=self.track_key, s=self.session)
        return params

    @staticmethod
    def make_url(params):
        return '/L?%(params)s&%(random)d' % dict(
            params='&'.join(['='.join([k, quote_plus(str(v))]) for k, v in params.items() if v is not None]),
            random=randint(0, 999999),
        )

    @staticmethod
    def loc(location):
        if not location:
            return ''
        if PY2:
            location = unicode(bytes(location), 'utf-8')
        location = location.encode('utf-8')
        return quote_plus(re.sub(br'#.+$', b'', location), safe=b'/:=?&')

    def identify(self, email):
        self.track(direction=self.DIR_E, event=['identify', email])

    def track(self, direction=DIR_I, location='', referrer='', event=None):
        assert direction in self.DIR_ALLOWED, \
            "Invalid direction parameter. It must be one of %s" % ', '.join(self.DIR_ALLOWED)

        referrer = self.loc(referrer) or self.last_location if self.auto_referrer else self.loc(referrer)
        self.last_location = location = self.loc(location or self.base_location)
        params = self.make_params()
        params.update(d=direction, l=location, r=referrer)

        if event:
            assert isinstance(event, list) and 0 < len(event) < 4, "Invalid event parameter"
            params.update(e=json.dumps([event], ensure_ascii=False))

        url = self.make_url(params)

        conn = HTTPSConnection(self.TRACK_URL)
        conn.request('GET', url, headers=self.headers)
        conn.getresponse()
