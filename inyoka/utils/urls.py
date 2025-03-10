"""
    inyoka.utils.urls
    ~~~~~~~~~~~~~~~~~

    This module implements unicode aware unicode functions.  It also allows
    to build urls for different subdomains using the `href` function.


    :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from urllib.parse import quote, quote_plus

from django.conf import settings
from django.contrib.auth.models import Group
from django.utils.encoding import force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django_hosts.resolvers import get_host, get_host_patterns


def href(_module='portal', *parts, **query):
    """Generates an internal URL for different subdomains."""
    anchor = query.pop('_anchor', None)
    append_slash = _module not in ['static', 'media']
    path = '/'.join(quote(force_str(x)) for x in parts if x is not None)

    if not append_slash:
        base_url = {
            'media': settings.MEDIA_URL,
            'static': settings.STATIC_URL,
        }[_module].rstrip('/')
    else:
        subdomain = get_host(_module).regex
        subdomain = subdomain + '.' if subdomain else ''
        base_url = '%s://%s%s' % (settings.INYOKA_URI_SCHEME, subdomain, settings.BASE_DOMAIN_NAME)

    return '%s/%s%s%s%s' % (
        base_url,
        path,
        append_slash and path and not path.endswith('/') and '/' or '',
        query and '?' + urlencode(query) or '',
        anchor and '#' + quote_plus(force_str(anchor)) or ''
    )


def url_for(obj, action=None, **kwargs):
    """
    Get the URL for an object.  As we are not using django contrib stuff
    any more this method is not useful any more but no it isn't because
    django does ugly things with `get_absolute_url` so we have to do that.
    """
    if hasattr(obj, 'get_absolute_url'):
        if action is not None:
            return obj.get_absolute_url(action, **kwargs)
        return obj.get_absolute_url(**kwargs)
    if isinstance(obj, Group):
        if action == 'edit':
            return href('portal', 'group', obj.name, 'edit')
        return href('portal', 'group', obj.name)
    raise TypeError('type %r has no url' % obj.__class__)


def is_safe_domain(url):
    """
    Check whether `url` points to the same host as inyoka

    Return ``True`` if the url is a safe redirection (i.e. it doesn't point to
    a different host and uses a safe scheme).
    Always returns ``False`` on an empty url.
    """
    if isinstance(url, bytes):
        url = url.decode()

    services = (host.regex for host in get_host_patterns())
    # service > service.domain.tld:
    safe_hostnames = [f'{service}.{settings.BASE_DOMAIN_NAME}'.lstrip('.') for service in services]
    # Only one successfully matching is_safe_url() must match:
    for hostname in safe_hostnames:
        if url_has_allowed_host_and_scheme(url, allowed_hosts=hostname):
            return True
    return False
