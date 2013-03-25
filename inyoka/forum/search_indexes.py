import datetime
from haystack import indexes
from inyoka.forum.models import Post


class PostIndex(indexes.SearchIndex, indexes.Indexable):
    pub_date = indexes.DateTimeField(model_attr='pub_date')
    hidden = indexes.BooleanField(model_attr='hidden')
    text = indexes.CharField(document=True, use_template=True)
    has_revision = indexes.BooleanField(model_attr='has_revision')
    has_attachments = indexes.BooleanField(model_attr='has_attachments')

    author = indexes.CharField(model_attr='author__username')
    topic = indexes.CharField(model_attr='topic__title')
    topic_slug = indexes.CharField(model_attr='topic__slug')

    def get_model(self):
        return Post

    def get_updated_field(self):
        return 'pub_date'

    def index_queryset(self, using=None):
        """Used when the entire index for the model is updated."""
        return self.get_model().objects.all()