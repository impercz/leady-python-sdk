# leady-python-sdk

[Leady](https://leady.cz) SDK for Python

With this package you can track events to [Leady](https://leady.cz) 
from your backend application. 

If you use [Django framework](https://www.djangoproject.com), 
you can combine tracking from backend and frontend with Leady JS code.
Also you can identify users persistently through `leady_cookie`.

## Installation

Requirements:

 * Tested with Python 2.7 and 3.5
 * Django if you want use `DjangoLeadyTracker`

You can install via `pip`:

```shell
pip install leady
```

## `LeadyTracker` usage

Initialize tracker with `track_key` obtained from [Leady](http://leady.cz) and domain (or application identifier).

```python
from leady import LeadyTracker
l = LeadyTracker('track_key', 'domain.tld')
```

Identify your customer. You can set few other parameters like `user_agent`,
`ip_address`, `url`.

```python
l.identify('user@example.com', user_agent='', ip_address='', url='')
```

If you don't want track events, you can push identity immediatelly.

```python
l.push()
```

Or you can start track events.

```python
l.track(event_name='Registrace', event_category='Letni kampan', event_value=1000)
```

Events are pushed immediatelly by default, but you can postpone it.

```python
l.track('Registrace', 'Letni kampan', push=False)
l.track('Login', 'Letni kampan', push=False)

# ...

l.push()
```

## `DjangoLeadyTracker` usage

```python
from leady import DjangoLeadyTracker

def some_view(request, *args):
    l = DjangoLeadyTracker('track_key', request)    
    l.identify('user@example.com')
    
    # ...

    l.track('download', 'report')

    # ...

    # render JS code that push events to template
    response = render(request, 'some_template.html', {'leady_code': l.js_code(), 'foo' : 'bar', })

    # If you want to track events from backend, you need to set leady cookie
    l.set_cookie(response)

    return response
```

