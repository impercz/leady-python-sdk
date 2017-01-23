from __future__ import print_function, unicode_literals

import json
import re
import uuid
from collections import OrderedDict
from random import randint

try:
    from urllib.parse import urlencode, quote_plus
    from http.client import HTTPSConnection
    PY2 = False
except ImportError:
    from urllib import urlencode, quote_plus
    from httplib import HTTPSConnection
    PY2 = True


class LeadyTrackerError(Exception):
    pass


class InvalidInputError(LeadyTrackerError):

    def __init__(self, message):
        super(InvalidInputError, self).__init__(message)

        if isinstance(message, list):
            self.error_list = []
            for message in message:
                if not isinstance(message, InvalidInputError):
                    message = InvalidInputError(message)
                self.error_list.extend(message.error_list)
        else:
            self.message = message
            self.error_list = [self]

    def __iter__(self):
        for error in self.error_list:
            yield error.message

    def __str__(self):
        return repr(list(self))

    def __repr__(self):
        return 'InvalidInputError(%s)' % self


class LeadyTracker(object):

    TRACKING_HOST = 't.leady.com'
    SUPPORTED_PARAM_KEYS = 'kdslrbuoe'
    DIRS_ALLOWED = 'ioe'
    DIR_I, DIR_O, DIR_E = DIRS_ALLOWED

    def __init__(self, track_key, auto_referrer=True, session=None, base_location='', user_agent='',
                 http_timeout=1, raise_errors=False):
        err = []

        try:
            track_key = str(track_key)
        except UnicodeEncodeError:
            err.append("Invalid track_key parameter")

        if not len(track_key) == 16:
            err.append("Invalid length of track_key parameter")

        if len(user_agent) > 255:
            err.append("Too long user_agent parameter")

        if len(base_location) > 155:
            err.append("Too long base_location parameter")

        if session is None:
            session = uuid.uuid4()

        if session and not isinstance(session, uuid.UUID):
            try:
                session = uuid.UUID(session)
            except ValueError:
                err.append(
                    "Invalid session parameter, expected UUID str, got %(type)s: %(value)s" % dict(
                        type=type(session),
                        value=session,
                    )
                )

        if err:
            raise InvalidInputError(err)

        self.session = str(session)
        self.track_key = track_key
        self.auto_referrer = auto_referrer
        self.base_location = base_location
        self.headers = {'User-Agent': user_agent} if user_agent else {}
        self.last_location = ''
        self.http_timeout = http_timeout
        self.raise_errors = raise_errors

    def _make_params(self):
        params = OrderedDict(
            (k, '') for k in self.SUPPORTED_PARAM_KEYS
        )
        params.update(
            k=self.track_key,
            s=self.session,
        )
        return params

    @staticmethod
    def _make_path(params):
        return '/L?%(params)s&%(random)d' % dict(
            params=urlencode(params),
            random=randint(0, 999999),
        )

    @staticmethod
    def _loc(location):
        if not location:
            return ''

        if PY2:
            location = unicode(
                bytes(location),
                'utf-8'
            )

        location = location.encode('utf-8')

        return quote_plus(
            re.sub(br'#.+$', b'', location),
            safe=b'/:=?&',
        )

    def identify(self, email):
        self.track(
            direction=self.DIR_E,
            event=['identify', email],
        )

    def track(self, direction=DIR_I, location='', referrer='', event=None):
        if direction not in self.DIRS_ALLOWED:
            raise InvalidInputError(
                "Invalid direction parameter. It must be one of '%s'" % "', '".join(self.DIRS_ALLOWED)
            )

        referrer = (self._loc(referrer) or self.last_location) if self.auto_referrer else self._loc(referrer)
        self.last_location = location = self._loc(location or self.base_location)

        params = self._make_params()
        params.update(
            d=direction,
            l=location,
            r=referrer,
        )

        if event is not None:
            if not isinstance(event, list) or not 0 < len(event) < 4:
                raise InvalidInputError("Invalid event parameter, use event=[name, category, value]")

            if len(event) == 3 and not isinstance(event[2], int):
                raise InvalidInputError("Invalid event value parameter")

            if not event[0] == 'identify':
                event.insert(0, 'event')

            params.update(
                e=json.dumps(
                    [event],
                    ensure_ascii=False,
                ),
            )
        path = self._make_path(params)

        try:
            conn = HTTPSConnection(self.TRACKING_HOST, timeout=self.http_timeout)
            conn.request(
                'GET',
                path,
                headers=self.headers,
            )
        except Exception:
            if self.raise_errors:
                raise
