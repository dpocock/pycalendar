# Copyright

import logging as _logging
import urllib.request as _urllib_request

from . import USER_AGENT as _USER_AGENT
from . import entry as _entry


_LOG = _logging.getLogger(__name__)


class Feed (set):
    r"""An iCalendar feed (:RFC:`5545`)

    Figure out where the example feed is located, relative to the
    directory from which you run this doctest (i.e., the project's
    root directory).

    >>> import os
    >>> root_dir = os.curdir
    >>> data_file = os.path.abspath(os.path.join(
    ...         root_dir, 'test', 'data', 'geohash.ics'))
    >>> url = 'file://{}'.format(data_file.replace(os.sep, '/'))

    Create a new feed pointing to this URL.

    >>> f = Feed(url=url)
    >>> f  # doctest: +ELLIPSIS
    <Feed url:file://.../test/data/geohash.ics>
    >>> print(f)
    <BLANKLINE>

    Load the feed content.

    >>> f.fetch()

    The ``.__str__`` method displays the feed content using Python's
    universal newlines.

    >>> print(f)  # doctest: +REPORT_UDIFF
    BEGIN:VCALENDAR
    VERSION:2.0
    PRODID:-//Example Calendar//NONSGML v1.0//EN
    BEGIN:VEVENT
    UID:2013-06-30@geohash.invalid
    DTSTAMP:2013-06-30T00:00:00Z
    DTSTART;VALUE=DATE:20130630
    DTEND;VALUE=DATE:20130701
    SUMMARY:XKCD geohashing\, Boston graticule
    URL:http://xkcd.com/426/
    LOCATION:Snow Hill\, Dover\, Massachusetts
    GEO:42.226663,-71.28676
    END:VEVENT
    END:VCALENDAR

    To get the CRLF line endings specified in :RFC:`5545`, use the
    ``.write`` method.

    >>> import io
    >>> stream = io.StringIO()
    >>> f.write(stream=stream)
    >>> stream.getvalue()  # doctest: +ELLIPSIS
    'BEGIN:VCALENDAR\r\nVERSION:2.0\r\n...END:VCALENDAR\r\n'

    You can also iterate through events:

    >>> for event in f:
    ...     print(repr(event))
    ...     print(event)
    <Entry type:VEVENT>
    BEGIN:VEVENT
    UID:2013-06-30@geohash.invalid
    DTSTAMP:2013-06-30T00:00:00Z
    DTSTART;VALUE=DATE:20130630
    DTEND;VALUE=DATE:20130701
    SUMMARY:XKCD geohashing\, Boston graticule
    URL:http://xkcd.com/426/
    LOCATION:Snow Hill\, Dover\, Massachusetts
    GEO:42.226663,-71.28676
    END:VEVENT
    """
    def __init__(self, url, content=None, user_agent=None):
        super(Feed, self).__init__()
        self.url = url
        self.content = content
        if user_agent is None:
            user_agent = _USER_AGENT
        self.user_agent = user_agent

    def __str__(self):
        if self.content:
            return self.content.replace('\r\n', '\n').strip()
        return ''

    def __repr__(self):
        return '<{} url:{}>'.format(type(self).__name__, self.url)

    def fetch(self, force=False):
        if self.content is None or force:
            self._fetch()
            self.process()

    def _fetch(self):
        request = _urllib_request.Request(
            url=self.url,
            headers={
                'User-Agent': self.user_agent,
                },
            )
        with _urllib_request.urlopen(url=request) as f:
            info = f.info()
            content_type = info.get('Content-type', None)
            if content_type != 'text/calendar':
                raise ValueError(content_type)
            byte_content = f.read()
        self.content = str(byte_content, encoding='UTF-8')

    def process(self):
        _LOG.info('{!r}: processing {} content characters'.format(
            self, len(self.content)))
        entry = None
        stack = []
        for i,line in enumerate(self.content.split('\r\n')):
            if line.startswith('BEGIN:'):
                _type = line.split(':', 1)[1]
                _LOG.info('{!r}: begin {}'.format(self, _type))
                stack.append(_type)
                if len(stack) == 2:
                    if entry:
                        raise ValueError('double entry by line {}'.format(i))
                    entry = _entry.Entry(type=_type, content=[])
            _LOG.info(stack)
            if entry:
                entry.content.append(line)
            if line.startswith('END:'):
                _type = line.split(':', 1)[1]
                _LOG.info('{!r}: end {}'.format(self, _type))
                if not stack or _type != stack[-1]:
                    raise ValueError(
                        ('closing {} on line {}, but current stack is {}'
                         ).format(_type, i, stack))
                stack.pop(-1)
                if len(stack) == 1:
                    entry.content.append('')  # trailing blankline
                    entry.content = '\r\n'.join(entry.content)
                    self.add(entry)
                    entry = None

    def write(self, stream):
        stream.write(self.content)
