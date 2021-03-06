# leady-python-sdk

[Leady](https://leady.com) SDK for Python

[![PyPI version](https://badge.fury.io/py/leady.svg)](https://badge.fury.io/py/leady)
[![Build Status](https://travis-ci.org/impercz/leady-python-sdk.svg?branch=master)](https://travis-ci.org/impercz/leady-python-sdk)


With this package you can track events to [Leady](https://leady.com)
from your backend application. 

## Installation

`leady` is tested with Python 2.7 and 3.5. You can install it via `pip`:

```shell
pip install leady
```

## Usage

Initialize tracker with `track_key` obtained from [Leady](https://leady.com).

Additional parameters you can use:

 * `auto_referrer`
 * `session` - `UUID4` if you want to save and reuse same session for customer
 * `base_location` - some parts of event tracking needs to provide location. 
   If you want to use it easier, zou can provide base location that will be used.
 * `user_agent` - similar as above.
 * `http_timeout` - specify custom `timeout` for connection to [Leady](https://leady.com)
 * `raise_errors` - raise errors when connection to leady fails. Default is `False` (silent).

```python
from leady import LeadyTracker
l = LeadyTracker('track_key', auto_referrer=True, base_location='https://monitora.cz', 
                 user_agent='Some-app/2.0', http_timeout=1, raise_errors=False)

# Track indentify event

l.identify('user@example.com')

# Track some visits and events

l.track(direction=l.DIR_I, location='https://example.com/entry')

event_value = 1000
l.track(direction=l.DIR_E, location='https://example.com/event', 
        event=['event_name', 'event_category', event_value])

l.track(l.DIR_O, location='https://example.com/bye')
```


## More advanced usage with web framework

You can reuse session if you want to track events through views...

Here is a simple example for the Django web framework:

```python
import uuid
from django.shortcuts import render
from leady import LeadyTracker

def first_view(request, *args):
    l = LeadyTracker('track_key')
    l.identify('user@example.com')
    
    # ...

    l.track('download', 'report')

    # ...

    # make response
    session = l.session
    response = render(request, 'template.html', {})
    response.set_cookie('leady_tracker_session', session, 60*60*24*365*2)

    return response


def second_view(request, *args):
    session = request.COOKIES.get('leady_tracker_session') or uuid.uuid4()
    l = LeadyTracker('track_key', session=session)
    
    # ...
```

## Even more advanced usage

You can also use pickle to reuse a tracker instance.

```python
import pickle
from leady import LeadyTracker

l = LeadyTracker('track_key')

# ... do some tracking ...

# save it where you want (redis, memcache, db)...
pl = pickle.dumps(l)
del l

# and load it back again
l = pickle.loads(pl)
```
