# -*- coding: utf-8 -*-
"""
    inyoka.planet.forms
    ~~~~~~~~~~~~~~~~~~~

    Formular for suggesting a new article.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django import forms
from django.core.validators import URLValidator
from inyoka.utils.forms import UserField
from inyoka.planet.models import Blog


class SuggestBlogForm(forms.Form):
    """Form to suggest a new blog url for the planet."""
    name = forms.CharField(label=u'Name des Blogs')
    url =  forms.URLField(label=u'URL')
    feed_url =  forms.URLField(label=u'Feed-URL', required=False)
    description = forms.CharField(label=u'Beschreibung',
        widget=forms.Textarea,
        help_text=(u'Die Beschreibung dient dem Ikhaya-Team '
              u'sich einen besseren Überblick zu verschaffen.'))
    mine = forms.BooleanField(label=u'Dieser Blog ist mein eigener',
                              required=False)
    contact_email = forms.EmailField(label=u'E-Mail-Adresse des Autors des '
                                           u'Blogs', required=False)



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
        if self.cleaned_data.get('active', False):
            validator = URLValidator(verify_exists=True)
        else:
            validator = URLValidator(verify_exists=False)
        validator(url)

    def clean_blog_url(self):
        self._validate_url(self.cleaned_data['blog_url'])
        return self.cleaned_data['blog_url']

    def clean_feed_url(self):
        self._validate_url(self.cleaned_data['feed_url'])
        return self.cleaned_data['feed_url']
