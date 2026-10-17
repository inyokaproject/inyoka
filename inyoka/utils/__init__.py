"""
    inyoka.utils
    ~~~~~~~~~~~~

    Various application independent utilities.

    :copyright: (c) 2007-2026 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.contrib.contenttypes.models import ContentType


def ctype(model):
    return ContentType.objects.get_for_model(model)


def get_request_context(request):
    if not request:
        return None

    mapping = {'ikhaya': 'ikhaya',
               'planet': 'planet',
               'wiki': 'wiki',
               'paste': 'pastebin',
               'forum': 'forum'}

    return mapping.get(request.subdomain, None)
