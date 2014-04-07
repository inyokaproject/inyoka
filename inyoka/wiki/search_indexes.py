# -*- coding: utf-8 -*-

from haystack import indexes
from celery_haystack.indexes import CelerySearchIndex
from inyoka.wiki.models import Page


class PageIndex(CelerySearchIndex, indexes.Indexable):

    updated = indexes.DateTimeField()

    title = indexes.CharField(boost=2.5)
    text = indexes.CharField(document=True)

    additional_model_attrs = ('name', 'topic', 'last_rev__text',
        'last_rev__change_date')

    def prepare_title(self, obj):
        return obj.title

    def prepare_text(self, obj):
        return obj.last_rev.text.parse().text.strip()

    def prepare_updated(self, obj):
        return obj.last_rev.change_date

    def get_model(self):
        return Page

    def index_queryset(self, using=None):
        """Used when the entire index for the model is updated.

        Automatically preloads related fields and optimizes the db query
        """
        fields = filter(None, (obj.model_attr for name, obj in self.fields.items()))
        fields = tuple(set(fields) | set(PageIndex.additional_model_attrs))
        related_fields = tuple(set(name for name in fields if '__' in name))
        return self.get_model().objects.select_related(*related_fields) \
                                         .only(*fields) \
                                         .all()
