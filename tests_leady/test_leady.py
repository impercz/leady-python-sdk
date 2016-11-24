# coding: utf-8

import pickle
import pytest
import uuid

from leady import LeadyTracker, LeadyTrackerError, InvalidInputError

HTTP_HOST = 'imper.cz'
HTTP_X_FORWARDED_FOR = '1.2.3.4'
HTTP_USER_AGENT = 'Browser/2.0'
TEST_KEY = 'a' * 16
TEST_LOCATION = 'https://example.com/?hallo=there are lions&12345#remove-thi-part-please&asd=2'
TEST_LOCATION_2 = 'https://example.com/?hallo=žluťoučký-kůň#remove-thi-part-please&asd=2'


def test_invalid_track_key():
    with pytest.raises(InvalidInputError) as exc_info:
        LeadyTracker('asd')
    assert 'Invalid length of track_key parameter' in str(exc_info.value)


def test_multiple_invalid_params():
    with pytest.raises(InvalidInputError) as exc_info:
        LeadyTracker('asd', session='123', base_location='a'*500)
    assert len(list(exc_info.value)) == 3
    assert 'Invalid length of track_key parameter' in str(list(exc_info.value)[0])
    assert 'Too long base_location parameter' in str(list(exc_info.value)[1])
    assert 'Invalid session parameter, expected UUID str' in str(list(exc_info.value)[2])


# noinspection PyProtectedMember
def test_locations_strip_encode():
    assert LeadyTracker._loc(TEST_LOCATION) == 'https://example.com/?hallo=there+are+lions&12345'
    assert LeadyTracker._loc(TEST_LOCATION_2) == 'https://example.com/?hallo=%C5%BElu%C5%A5ou%C4%8Dk%C3%BD-k%C5%AF%C5%88'


# noinspection PyProtectedMember
def test_make_params():
    s = uuid.uuid4()
    t = LeadyTracker(TEST_KEY, session=s, base_location='https://example.com')
    p = t._make_params()
    assert ''.join(p.keys()) == t.SUPPORTED_PARAM_KEYS
    assert p['s'] == str(s)
    assert p['k'] == TEST_KEY


# noinspection PyProtectedMember
def test_make_path():
    s = uuid.uuid4()
    t = LeadyTracker(TEST_KEY, session=s, base_location='https://example.com')
    p = t._make_params()
    p.update(d=t.DIR_I, l='here')
    l = t._make_path(p)
    assert l.startswith('/L?k=aaaaaaaaaaaaaaaa&d=i&s=%s&l=here&r=&b=&u=&o=&e=&' % s)


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
    with pytest.raises(InvalidInputError) as exc_info:
        t.track(direction='AA')
    assert 'Invalid direction parameter' in str(exc_info.value)


def test_bad_event_param():
    t = LeadyTracker(TEST_KEY)
    msgs = [
        'Invalid event parameter',
        'Invalid event value parameter'
    ]
    bad_evts = (
        ('string', 0),  # not list
        (['a', 'b', 100, 200], 0),  # len > 3
        ([], 0),  # len < 1

        # wrong value types
        (['a', 'b', 2.21], 1),
        (['a', 'b', ''], 1),
        (['a', 'b', None], 1),
        (['a', 'b', []], 1),
        (['a', 'b', {}], 1),
    )

    for e, m in bad_evts:
        with pytest.raises(InvalidInputError) as exc_info:
            t.track(event=e)
        assert msgs[m] in str(exc_info.value)
