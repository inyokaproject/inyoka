"""
    inyoka.ikhaya.forms
    ~~~~~~~~~~~~~~~~~~~

    Forms for the Ikhaya.

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, time as dt_time

from django import forms
from django.utils.timezone import get_current_timezone
from django.utils.translation import gettext_lazy

import pytz

from inyoka.ikhaya.models import Event, Article, Category, Suggestion
from inyoka.portal.models import StaticFile
from inyoka.utils.forms import (UserField, TimeWidget, DateWidget,
    DateTimeField, StrippedCharField)
from inyoka.utils.dates import datetime_to_timezone
from inyoka.utils.text import slugify


class SuggestArticleForm(forms.ModelForm):

    def save(self, user, commit=True):
        suggestion = super().save(commit=False)
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
    text = StrippedCharField(label=gettext_lazy('Text'), widget=forms.Textarea,
             help_text=gettext_lazy('To refer to another comment, you '
               'can write <code>@commentnumber</code>.<br />'
               'Clicking on “reply” will automatically insert this code.'))


class EditArticleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        readonly = kwargs.pop('readonly', False)
        if instance:
            initial = kwargs.setdefault('initial', {})
            if instance.pub_datetime != instance.updated:
                initial['updated'] = instance.updated
            initial['author'] = instance.author.username
        super().__init__(*args, **kwargs)
        # Following stuff is in __init__ to keep helptext etc intact.
        self.fields['icon'].queryset = StaticFile.objects.filter(is_ikhaya_icon=True)
        if readonly:
            for field in ('subject', 'intro', 'text'):
                self.fields[field].widget.attrs['readonly'] = True

    author = UserField(label=gettext_lazy('Author'), required=True)
    updated = DateTimeField(label=gettext_lazy('Last update'),
                help_text=gettext_lazy('If you keep this field empty, the '
                    'publication date will be used.'),
                localize=True, required=False)

    def save(self):
        instance = super().save(commit=False)
        if 'pub_date' in self.cleaned_data and (not instance.pk or
                not instance.public or self.cleaned_data.get('public', None)):
            instance.pub_date = self.cleaned_data['pub_date']
            instance.pub_time = self.cleaned_data['pub_time']
        if self.cleaned_data.get('updated', None):
            instance.updated = self.cleaned_data['updated']
        elif {'pub_date', 'pub_time'} in set(self.cleaned_data.keys()):
            instance.updated = date_time_to_datetime(
                self.cleaned_data['pub_date'],
                self.cleaned_data['pub_time'])
        instance.save()
        return instance

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        pub_date = self.cleaned_data.get('pub_date', None)
        if slug and pub_date:
            slug = slugify(slug)
            q = Article.objects.filter(slug=slug, pub_date=pub_date)
            if self.instance.pk:
                q = q.exclude(id=self.instance.pk)
            if q.exists():
                raise forms.ValidationError(gettext_lazy('There already '
                            'exists an article with this slug!'))
        return slug

    class Meta:
        model = Article
        exclude = ['updated', 'comment_count']
        widgets = {
            'subject': forms.TextInput(attrs={'size': 50}),
            'intro': forms.Textarea(attrs={'rows': 3}),
            'text': forms.Textarea(attrs={'rows': 15}),
            'pub_date': DateWidget(),
            'pub_time': TimeWidget(),
        }


class EditPublicArticleForm(EditArticleForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields['pub_date']
        del self.fields['pub_time']

    class Meta(EditArticleForm.Meta):
        exclude = EditArticleForm.Meta.exclude + ['slug']


class EditCategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
                dt = datetime_to_timezone(datetime.combine(
                    event.date, event.time or dt_time(0)))
                event.date = dt.date()
                event.time = dt.time()

            if event.endtime is not None:
                dt_end = datetime_to_timezone(datetime.combine(
                    event.enddate or event.date, event.endtime))
                event.enddate = dt_end.date()
                event.endtime = dt_end.time()

        super().__init__(*args, **kwargs)

    def save(self, user):
        event = super().save(commit=False)
        convert = (lambda v: get_current_timezone().localize(v) \
                            .astimezone(pytz.utc).replace(tzinfo=None))
        # Convert local timezone to unicode
        if event.date and event.time is not None:
            d = convert(datetime.combine(
                event.date, event.time or dt_time(0)
            ))
            event.date = d.date()
            event.time = d.time()
        if event.endtime is not None:
            d = convert(datetime.combine(
                event.enddate or event.date, event.endtime
            ))
            event.enddate = d.date()
            event.endtime = event.time is not None and d.time()

        event.author = user
        event.save()

        return event

    def clean(self):
        cleaned_data = self.cleaned_data
        startdate = cleaned_data.get('date')
        enddate = cleaned_data.get('enddate')
        if startdate and enddate and enddate < startdate:
            self._errors['enddate'] = self.error_class([gettext_lazy('The '
                'end date must occur after the start date.')])
            del cleaned_data['enddate']
        elif startdate == enddate:
            starttime = cleaned_data.get('time')
            endtime = cleaned_data.get('endtime')
            if starttime and endtime and endtime < starttime:
                self._errors['endtime'] = self.error_class([gettext_lazy('The '
                      'end time must occur after the start time.')])
                del cleaned_data['endtime']

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
    visible = forms.BooleanField(label=gettext_lazy('Display event?'),
                required=False)

    class Meta(NewEventForm.Meta):
        exclude = ['author', 'slug']
