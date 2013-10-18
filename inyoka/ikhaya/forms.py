# -*- coding: utf-8 -*-
"""
    inyoka.ikhaya.forms
    ~~~~~~~~~~~~~~~~~~~

    Forms for the Ikhaya.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import time as dt_time

from django import forms
from django.utils.translation import ugettext_lazy

import pytz
from inyoka.utils.forms import (
    UserField,
    TimeWidget,
    DateWidget,
    DateTimeField,
    StrippedCharField
)
from inyoka.utils.dates import (
    get_user_timezone,
    datetime_to_timezone,
    date_time_to_datetime
)
from inyoka.portal.models import StaticFile
from inyoka.ikhaya.models import Event, Article, Category, Suggestion


class SuggestArticleForm(forms.ModelForm):

    def save(self, user, commit=True):
        suggestion = super(SuggestArticleForm, self).save(commit=False)
        suggestion.author = user
        if commit:
            suggestion.save()
        return suggestion

    class Meta:
        model = Suggestion
        fields = ('title', 'intro', 'text', 'notes')
        widgets = {
            'intro': forms.Textarea({'rows': 4})
        }


class EditCommentForm(forms.Form):
    text = StrippedCharField(label=ugettext_lazy(u'Text'), widget=forms.Textarea,
             help_text=ugettext_lazy(u'To refer to another comment, you '
               u'can write <code>@commentnumber</code>.<br />'
               u'Clicking on “reply” will automatically insert this code.'))


class EditArticleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        readonly = kwargs.pop('readonly', False)
        if instance:
            initial = kwargs.setdefault('initial', {})
            initial['pub_date'] = instance.pub_datetime
            if instance.pub_datetime != instance.updated:
                initial['updated'] = instance.updated
            initial['author'] = instance.author.username
        super(EditArticleForm, self).__init__(*args, **kwargs)
        # Following stuff is in __init__ to keep helptext etc intact.
        self.fields['icon'].queryset = StaticFile.objects.filter(is_ikhaya_icon=True)
        if readonly:
            for field in ('subject', 'intro', 'text'):
                self.fields[field].widget.attrs['readonly'] = True

    author = UserField(label=ugettext_lazy(u'Author'), required=True)
    pub_date = DateTimeField(label=ugettext_lazy(u'Publication date'),
                help_text=ugettext_lazy(u'If the date is in the future, '
                    u'the article will not appear until then.'),
                localize=True, required=True)
    updated = DateTimeField(label=ugettext_lazy(u'Last update'),
                help_text=ugettext_lazy(u'If you keep this field empty, the '
                    u'publication date will be used.'),
                localize=True, required=False)

    def save(self):
        instance = super(EditArticleForm, self).save(commit=False)
        if 'pub_date' in self.cleaned_data and (not instance.pk or
                not instance.public or self.cleaned_data.get('public', None)):
            instance.pub_date = self.cleaned_data['pub_date'].date()
            instance.pub_time = self.cleaned_data['pub_date'].time()
        if self.cleaned_data.get('updated', None):
            instance.updated = self.cleaned_data['updated']
        elif 'pub_date' in self.cleaned_data:
            instance.updated = self.cleaned_data['pub_date']
        instance.save()
        return instance

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        pub_date = self.cleaned_data.get('pub_date', None)
        if not pub_date:
            return slug  # invalid anyway as pub_date is required
        pub_date = get_user_timezone().localize(pub_date) \
                    .astimezone(pytz.utc).replace(tzinfo=None).date()
        if slug:
            q = Article.objects.filter(slug=slug, pub_date=pub_date)
            if 'article_id' in self.cleaned_data:
                q = q.exclude(id=self.cleaned_data['article_id'])
            if q.exists():
                raise forms.ValidationError(ugettext_lazy(u'There already '
                            u'exists an article with this slug!'))
        return slug

    class Meta:
        model = Article
        exclude = ['pub_date', 'pub_time', 'updated', 'comment_count']
        widgets = {
            'subject': forms.TextInput(attrs={'size': 50}),
            'intro': forms.Textarea(attrs={'rows': 3}),
            'text': forms.Textarea(attrs={'rows': 15}),
        }


class EditPublicArticleForm(EditArticleForm):
    def __init__(self, *args, **kwargs):
        super(EditPublicArticleForm, self).__init__(*args, **kwargs)
        del self.fields['pub_date']

    class Meta(EditArticleForm.Meta):
        exclude = EditArticleForm.Meta.exclude + ['slug']


class EditCategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EditCategoryForm, self).__init__(*args, **kwargs)
        # Following stuff is in __init__ to keep helptext etc intact.
        self.fields['icon'].queryset = StaticFile.objects.filter(is_ikhaya_icon=True)

    class Meta:
        model = Category
        exclude = ['slug']


class NewEventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        event = kwargs.get('instance', None)
        if event:  # Adjust datetime to local timezone
            if event.date and event.time is not None:
                dt = datetime_to_timezone(date_time_to_datetime(
                    event.date, event.time or dt_time(0)))
                event.date = dt.date()
                event.time = dt.time()

            if event.endtime is not None:
                dt_end = datetime_to_timezone(date_time_to_datetime(
                    event.enddate or event.date, event.endtime))
                event.enddate = dt_end.date()
                event.endtime = dt_end.time()

        super(NewEventForm, self).__init__(*args, **kwargs)

    def save(self, user):
        event = super(NewEventForm, self).save(commit=False)
        convert = (lambda v: get_user_timezone().localize(v) \
                            .astimezone(pytz.utc).replace(tzinfo=None))
        # Convert local timezone to unicode
        if event.date and event.time is not None:
            d = convert(date_time_to_datetime(
                event.date, event.time or dt_time(0)
            ))
            event.date = d.date()
            event.time = d.time()
        if event.endtime is not None:
            d = convert(date_time_to_datetime(
                event.enddate or event.date, event.endtime
            ))
            event.enddate = d.date()
            event.endtime = event.time is not None and d.time()

        event.author = user
        event.save()

        return event

    def clean(self):
        cleaned_data = self.cleaned_data
        start = cleaned_data.get('date')
        end = cleaned_data.get('enddate')
        if end and end < start:
            self._errors['enddate'] = self.error_class([ugettext_lazy(u'The '
                u'end date must occur after the start date.')])
            del cleaned_data['enddate']

        return cleaned_data

    class Meta:
        model = Event
        widgets = {
            'date': DateWidget,
            'time': TimeWidget,
            'enddate': DateWidget,
            'endtime': TimeWidget,
        }
        exclude = ['author', 'slug', 'visible']


class EditEventForm(NewEventForm):
    visible = forms.BooleanField(label=ugettext_lazy(u'Display event?'),
                required=False)

    class Meta(NewEventForm.Meta):
        exclude = ['author', 'slug']
