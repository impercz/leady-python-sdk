# coding: utf-8

import pickle
import pytest
import uuid

try:
    from urllib.parse import urlencode
    from http.client import HTTPSConnection, HTTPException
except ImportError:
    from urllib import urlencode
    from httplib import HTTPSConnection, HTTPException


from leady import LeadyTracker, LeadyTrackerError

HTTP_HOST = 'imper.cz'
HTTP_X_FORWARDED_FOR = '1.2.3.4'
HTTP_USER_AGENT = 'Browser/2.0'
TEST_KEY = 'a' * 16
TEST_LOCATION = 'https://example.com/?hallo=there are lions&12345#remove-thi-part-please&asd=2'
TEST_LOCATION_2 = 'https://example.com/?hallo=žluťoučký-kůň#remove-thi-part-please&asd=2'


def test_invalid_track_key():
    with pytest.raises(AssertionError) as exc_info:
        LeadyTracker('asd')
    assert 'Invalid track_key parameter' in str(exc_info.value)


def test_locations_strip_encode():
    assert LeadyTracker.loc(TEST_LOCATION) == 'https://example.com/?hallo=there+are+lions&12345'
    assert LeadyTracker.loc(TEST_LOCATION_2) == 'https://example.com/?hallo=%C5%BElu%C5%A5ou%C4%8Dk%C3%BD-k%C5%AF%C5%88'


def test_make_params():
    s = uuid.uuid4()
    t = LeadyTracker(TEST_KEY, session=s, base_location='https://example.com')
    p = t.make_params()
    assert ''.join(p.keys()) == t.SUPPORTED_PARAM_KEYS
    assert p['s'] == str(s)
    assert p['k'] == TEST_KEY


def test_make_url():
    s = uuid.uuid4()
    t = LeadyTracker(TEST_KEY, session=s, base_location='https://example.com')
    p = t.make_params()
    url = t.make_url(p)
    assert url.startswith('/L?k=aaaaaaaaaaaaaaaa&d=&s=%s&l=&r=&b=&u=&o=&e=&' % s)


def test_session():
    s = uuid.uuid4()
    sstr = str(s)
    t = LeadyTracker(TEST_KEY, session=s)
    assert t.session == sstr

    t = LeadyTracker(TEST_KEY, session=sstr)
    assert t.session == sstr

    with pytest.raises(LeadyTrackerError) as exc_info:
        LeadyTracker(TEST_KEY, session='bad')
    assert 'Invalid session parameter' in str(exc_info)


def test_pickle():
    t = LeadyTracker(TEST_KEY, base_location='http://a.aa')
    s = t.session
    pt = pickle.dumps(t)
    del t
    t = pickle.loads(pt)
    assert s == t.session


def test_bad_dir():
    t = LeadyTracker(TEST_KEY)
    with pytest.raises(AssertionError) as exc_info:
        t.track(direction='AA')
    assert 'Invalid direction parameter' in str(exc_info)
