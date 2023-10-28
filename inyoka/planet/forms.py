"""
    inyoka.planet.forms
    ~~~~~~~~~~~~~~~~~~~

    Formular for suggesting a new article.

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django import forms
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy

from inyoka.utils.forms import UserField
from inyoka.planet.models import Blog


class SuggestBlogForm(forms.Form):
    """Form to suggest a new blog url for the planet."""
    name = forms.CharField(label=gettext_lazy('Name of the blog'))
    url = forms.URLField(label=gettext_lazy('URL'))
    feed_url = forms.URLField(label=gettext_lazy('Feed URL'), required=False)
    description = forms.CharField(label=gettext_lazy('Description'),
        widget=forms.Textarea)
    mine = forms.BooleanField(label=gettext_lazy('This is my own blog'),
                              required=False)
    contact_email = forms.EmailField(
        label=gettext_lazy('Email address of the blog author'),
        required=False)


class EditBlogForm(forms.ModelForm):
    user = UserField(required=False)
    active = forms.BooleanField(required=False)

    class Meta:
        model = Blog
        #: NOTE: `active` must be before blog/feed_url so that we can
        #        check their validity context sensitive
        fields = ('active', 'name', 'description', 'blog_url', 'feed_url',
                  'user', 'icon')

    def _validate_url(self, url):
        # Since Django 1.5 there is no `verify_exists` for the validator
        validator = URLValidator()
        validator(url)

    def clean_blog_url(self):
        self._validate_url(self.cleaned_data['blog_url'])
        return self.cleaned_data['blog_url']

    def clean_feed_url(self):
        self._validate_url(self.cleaned_data['feed_url'])
        return self.cleaned_data['feed_url']
