# -*- coding: utf-8 -*-

from haystack import indexes
from celery_haystack.indexes import CelerySearchIndex
from inyoka.ikhaya.models import Article


class ArticleIndex(CelerySearchIndex, indexes.Indexable):

    author = indexes.CharField(model_attr='author__username')
    category = indexes.CharField(model_attr='category__name', boost=1.125)
    category_slug = indexes.CharField(model_attr='category__slug')

    pub_date = indexes.DateTimeField()
    updated = indexes.DateTimeField(model_attr='updated')

    subject = indexes.CharField(model_attr='subject', boost=2.5)
    intro = indexes.CharField(boost=1.125)
    text = indexes.CharField(document=True)

    category_auto = indexes.EdgeNgramField(model_attr='category__name')

    additional_model_attrs = ('pub_date', 'pub_time', 'is_xhtml', 'text',
        'intro', 'comment_count', 'comments_enabled', 'icon__id', 'public',
        'slug')

    def prepare_pub_date(self, obj):
        return obj.pub_datetime

    def prepare_intro(self, obj):
        return obj.simplified_intro

    def prepare_text(self, obj):
        return obj.simplified_text

    def get_model(self):
        return Article

    def index_queryset(self, using=None):
        """Used when the entire index for the model is updated.

        Automatically preloads related fields and optimizes the db query
        """
        fields = filter(None, (obj.model_attr for name, obj in self.fields.items()))
        fields = tuple(set(fields) | set(ArticleIndex.additional_model_attrs))
        related_fields = tuple(set(name for name in fields if '__' in name))
        return self.get_model().published.select_related(*related_fields) \
                                         .only(*fields) \
                                         .all()
