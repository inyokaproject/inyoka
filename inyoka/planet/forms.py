# -*- coding: utf-8 -*-
"""
    inyoka.planet.forms
    ~~~~~~~~~~~~~~~~~~~

    Formular for suggesting a new article.

    :copyright: (c) 2007-2018 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django import forms
from django.utils.translation import ugettext_lazy

from inyoka.planet.models import Blog
from inyoka.utils.forms import UserField


class SuggestBlogForm(forms.Form):
    """Form to suggest a new blog url for the planet."""
    name = forms.CharField(label=ugettext_lazy(u'Name of the blog'))
    url = forms.URLField(label=ugettext_lazy(u'URL'))
    feed_url = forms.URLField(label=ugettext_lazy(u'Feed URL'), required=False)
    description = forms.CharField(label=ugettext_lazy(u'Description'),
                                  widget=forms.Textarea)
    mine = forms.BooleanField(label=ugettext_lazy(u'This is my own blog'),
                              required=False)
    contact_email = forms.EmailField(
        label=ugettext_lazy(u'Email address of the blog author'),
        required=False)


class EditBlogForm(forms.ModelForm):
    user = UserField(required=False)
    active = forms.BooleanField(required=False)

    class Meta:
        model = Blog
        fields = ('active', 'name', 'description', 'blog_url', 'feed_url',
                  'user', 'icon')
