import datetime
from haystack import indexes
from celery_haystack.indexes import CelerySearchIndex
from inyoka.forum.models import Post


class PostIndex(indexes.ModelSearchIndex, CelerySearchIndex, indexes.Indexable):

    class Meta:
        model = Post
        fields = ['author', 'topic', 'topic_slug', 'pub_date', 'hidden',
                  'text', 'has_revision', 'has_attachments', 'is_plaintext',
                  'topic_auto']

    author = indexes.CharField(model_attr='author__username')
    topic = indexes.CharField(model_attr='topic__title', boost=1.125)
    topic_slug = indexes.CharField(model_attr='topic__slug')

    ubuntu_version = indexes.CharField(model_attr='topic__ubuntu_version', null=True)
    ubuntu_distro = indexes.CharField(model_attr='topic__ubuntu_distro', null=True)

    pub_date = indexes.DateTimeField(model_attr='pub_date')
    hidden = indexes.BooleanField(model_attr='hidden')
    text = indexes.CharField(document=True)
    has_revision = indexes.BooleanField(model_attr='has_revision')
    has_attachments = indexes.BooleanField(model_attr='has_attachments')
    is_plaintext = indexes.BooleanField(model_attr='is_plaintext', stored=False)

    topic_auto = indexes.EdgeNgramField(model_attr='topic__title')

    def prepare_text(self, obj):
        return obj.stripped_text

    def get_updated_field(self):
        return 'pub_date'

    def index_queryset(self, using=None):
        """Used when the entire index for the model is updated.

        Automatically preloads related fields and optimizes the db query
        """
        fields = filter(None, (obj.model_attr for name, obj in self.fields.items()))
        fields = tuple(set(fields))
        related_fields = tuple(set(name for name in fields if '__' in fields))
        return (self.get_model().objects
                    .select_related(*related_fields)
                    .only(*fields)
                    .all())
