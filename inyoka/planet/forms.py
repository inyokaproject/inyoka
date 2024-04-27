"""
    inyoka.planet.forms
    ~~~~~~~~~~~~~~~~~~~

    Formular for suggesting a new article.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django import forms
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
        fields = ('active', 'name', 'description', 'blog_url', 'feed_url',
                  'user', 'icon')
