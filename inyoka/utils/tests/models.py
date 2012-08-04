from django.db import models
from django.utils.translation import ugettext_lazy
from pyes import TermsFilter
from inyoka.forum.acl import get_privileges, check_privilege
from inyoka.forum.models import Post, Forum
from inyoka.utils.search import search, Index, DocumentType
from inyoka.utils.urls import url_for, href
from inyoka.utils.database import JSONField


class JSONEntry(models.Model):
    f = JSONField(blank=True)


class Stanza(models.Model):
    data = models.CharField(max_length=250)



class StanzaDocumentType(DocumentType):
    name = 'stanza'
    model = Stanza

    mapping = {'properties': {
        'pk': {'type': 'integer', 'store': 'yes'},
        'data': {'type': 'string', 'store': 'yes'},
    }}



class StanzaIndex(Index):
    name = 'stanza'
    types = [StanzaDocumentType]


search.register(StanzaIndex)
