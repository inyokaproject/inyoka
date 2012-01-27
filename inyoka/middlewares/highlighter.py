# -*- coding: utf-8 -*-
"""
    inyoka.middlewares.highlighter
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This middleware checks the URL for a `highlight` parameter that contains
    of a list of whitespace separated searchwords we want to highlight.

    Keep in mind that this middleware does not stem the searchwords thus the
    number of highlighed words can (and will) be different from the number of
    matches in the original document.  To improve that this highlighter
    accepts some more word characters after the match to complete the
    highlighted word.  So ``'complet'`` highlighlights both ``'completion'``
    and ``'complete'`` but not ``'autocomplete'``.

    This middleware does not highlight within ``script``, ``textarea``,
    ``style``, and ``head``.  The ``head`` section is excluded because it's
    invisible for one and contains pseudo displayed elements like ``title``
    that could cause unexpected results when highlighted.

    This uses the `flashing` capabilities of inyoka.  Keep in mind that this
    sort of highlighting is quite expensive compared to a normal request.
    Maybe we can find a better solution in the future that doesn't split
    and ressamble the text.  This also evaluates dynamic requests into a
    plain string.  Thus if you have a request that uses streaming it will
    be buffered and then processed.


    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from werkzeug import url_decode
from inyoka.utils.html import escape
from inyoka.utils.http import HttpResponseRedirect
from inyoka.utils.flashing import flash, unflash


# referrer urls matching this regex will be allowed
_referrer_re = re.compile(
    r'https?://(www\.)?(google|altavista)\.(de|at|ch|com)'
)

_tag_re = re.compile(r'(<!--.*?-->|<[^>]*>)(?s)')
_tagname_re = re.compile(r'<(/)?([a-zA-Z0-9]+)(?=\s|>)')
_isolated = frozenset(('script', 'head', 'style', 'textarea', 'option'))
_umlaut_choices = [
    ('a',   ur'(?:a|ä)'),
    ('e',   ur'(?:e|é|è)'),
    ('ss',  ur'(?:ss|ß)'),
    ('sz',  ur'(?:sz|ß)'),
    ('ae',  ur'(?:ae|ä|æ)'),
    ('ue',  ur'(?:ue|ü)'),
    ('oe',  ur'(?:oe|ö|ø)')
]


def _make_replacer(words):
    def quote(x):
        rv = re.escape(x)
        for find, regex in _umlaut_choices:
            rv = rv.replace(find, regex)
        return rv

    def handle_match(match):
        return u'<span class="highlight">%s</span>' % match.group()

    sub = re.compile(ur'\b(%s)\w*\b(?iu)' % '|'.join(map(quote, words))).sub
    return lambda x: sub(handle_match, x)


class HighlighterMiddleware(object):
    """
    Highlight searchwords.  And flash a message that allows to disable the
    highlighting again.
    """

    def process_request(self, request):
        """
        During request processing we check either if there is a "highlight"
        parameter in the query string.  If not we check the referrer for a
        "q" or "query" parameter.  If any of the parameters have a proper
        value it's whitespace splitted and the search words are saved on
        the request object.
        """
        if request.method == 'GET':
            plain_url = request.path
            if 'highlight' in request.GET:
                search_words = request.GET['highlight']
                args = request.GET.copy()
                del args['highlight']
                if args:
                    plain_url += '?' + args.urlencode()
            # no referrer based highlighting for users with disabled
            # highlighting.
            elif not request.user.settings.get('highlight_search', True):
                referrer = request.META.get('HTTP_REFERER')
                if not referrer or '?' not in referrer:
                    return
                url, query = referrer.split('?', 1)
                if not _referrer_re.match(url):
                    return
                args = url_decode(query)
                search_words = args.get('q') or args.get('query')
                if request.GET:
                    plain_url += '?' + request.GET.urlencode()
            else:
                return
            if search_words:
                request.highlight_searchwords = search_words.lower().split()
                flash(u'Suchergebnisse werden hervorgehoben. Suchwörter '
                      u'<a class="hide_searchwords" href="%s">ausblenden</a>.'
                      % escape(plain_url),
                      classifier='middleware/hide_highlights')
            else:
                return HttpResponseRedirect(plain_url)

    def process_response(self, request, response):
        """
        If the content type is text/html, the value is proper utf-8, there is
        highlight information on the request object.
        """
        # because of redirects it could happen that we trigger the flashing
        # code multiple times.  To avoid that the user gets a flash for every
        # url in the redirect chain we remove all "middleware/hide_highlights"
        # flash messages left.  Normally a template rendering would remove
        # those messages automatically but in the case of an redirect it
        # does not.
        unflash(u'middleware/hide_highlights')

        try:
            if not getattr(request, 'highlight_searchwords', None) or \
               response['content-type'].split(';')[0] != 'text/html':
                return response
            data = response.content.decode('utf-8')
        except UnicodeError:
            return response

        sub = _make_replacer(request.highlight_searchwords)

        buffer = _tag_re.split(data)
        skip_to = None
        for idx, data in enumerate(buffer):
            if idx % 2 == 0 and not skip_to:
                buffer[idx] = sub(data)
            else:
                match = _tagname_re.match(data)
                if match is None:
                    continue
                closing, tag = match.groups()
                tag = tag.lower()
                if skip_to and closing and tag == skip_to:
                    skip_to = None
                elif not skip_to and not closing and tag in _isolated:
                    skip_to = tag

        response.content = u''.join(buffer).encode('utf-8')
        return response
