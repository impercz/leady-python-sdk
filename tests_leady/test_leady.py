# coding: utf-8

import pytest
import re
import uuid
from unittest import TestCase

from django.test import RequestFactory
from django.conf import settings

try:
    from urllib.parse import urlencode, quote, quote_plus
    from http.client import HTTPSConnection, HTTPException
except ImportError:
    from urllib import urlencode, quote, quote_plus
    from httplib import HTTPSConnection, HTTPException


from leady import LeadyTracker, DjangoLeadyTracker, LeadyTrackerError

settings.configure()

HTTP_HOST = 'imper.cz'
HTTP_X_FORWARDED_FOR = '1.2.3.4'
HTTP_USER_AGENT = 'Browser/2.0'
TEST_LOCATION = '/dashboard/?hallo=there are lions#remove-thi-part-please&asd=2'
EXPECTED_LOCATION = quote(re.sub(r'#.+$', '', TEST_LOCATION), safe="/:@&+$,-_.!~*'()?=")


class TrackerTests(TestCase):

    def setUp(self):
        super(TrackerTests, self).setUp()
        self.l = LeadyTracker('test', 'ěščřřžů')

    def test_push_raise(self):
        assert self.l._events == []
        with pytest.raises(LeadyTrackerError) as exc_info:
            self.l.push()
        assert 'identify()' in str(exc_info.value)

    def test_url_stripped(self):
        self.l.identify('a@a.aa', url=TEST_LOCATION)
        assert self.l._params['l'] == EXPECTED_LOCATION


class DjangoTrackerTests(TestCase):

    def setUp(self):
        super(DjangoTrackerTests, self).setUp()
        self.rf = RequestFactory(HTTP_HOST=HTTP_HOST, HTTP_X_FORWARDED_FOR=HTTP_X_FORWARDED_FOR,
                                 HTTP_USER_AGENT=HTTP_USER_AGENT)

    def test_get_meta_from_request(self):
        r = self.rf.get(TEST_LOCATION)
        l = DjangoLeadyTracker('a', r)
        assert l._identifier == 'imper.cz'
        assert l._params['p'] == HTTP_X_FORWARDED_FOR
        assert l._params['l'] == EXPECTED_LOCATION

    def test_session_id_generated(self):
        r = self.rf.get(TEST_LOCATION)
        l = DjangoLeadyTracker('a', r)
        assert l._params['s'] == l._cookie_value

    def test_session_from_request(self):
        r = self.rf.get(TEST_LOCATION)
        test_sid = uuid.uuid4()
        r.COOKIES[DjangoLeadyTracker._cookie_name] = test_sid
        l = DjangoLeadyTracker('a', r)
        assert l._params['s'] == test_sid
