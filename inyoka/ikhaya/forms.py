"""
    inyoka.ikhaya.forms
    ~~~~~~~~~~~~~~~~~~~

    Forms for the Ikhaya.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from datetime import time as dt_time

from django import forms
from django.forms import SplitDateTimeField
from django.utils import timezone as dj_timezone
from django.utils.timezone import get_current_timezone
from django.utils.translation import gettext_lazy

from inyoka.ikhaya.models import Article, Category, Event, Suggestion
from inyoka.portal.models import StaticFile
from inyoka.utils.dates import datetime_to_timezone
from inyoka.utils.forms import (
    NativeDateInput,
    NativeSplitDateTimeWidget,
    NativeTimeInput,
    StrippedCharField,
    UserField,
)
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
               'Clicking on “reply” will automatically insert this code.'), strip=False)


class EditArticleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        readonly = kwargs.pop('readonly', False)

        if instance:
            initial = kwargs.setdefault('initial', {})
            if instance.public:
                initial['updated'] = dj_timezone.now()
            initial['author'] = instance.author.username

        super().__init__(*args, **kwargs)

        self.fields['icon'].queryset = StaticFile.objects.filter(is_ikhaya_icon=True)
        if readonly:
            for field in ('subject', 'intro', 'text'):
                self.fields[field].widget.attrs['readonly'] = True

        if not instance:
            del self.fields['updated']

    author = UserField(label=gettext_lazy('Author'), required=True)

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        pub_datetime = self.cleaned_data.get('publication_datetime', None)

        if slug and pub_datetime:
            slug = slugify(slug)
            pub_date = pub_datetime.date()
            ## TODO truncate to date?
            q = Article.objects.filter(slug=slug, publication_datetime=pub_date)

            if self.instance.pk:
                q = q.exclude(id=self.instance.pk)

            if q.exists():
                raise forms.ValidationError(gettext_lazy('There already '
                            'exists an article with this slug!'))
        return slug

    class Meta:
        model = Article
        fields = ('subject', 'intro', 'text', 'author', 'category', 'icon', 'public', 'comments_enabled', 'updated', 'publication_datetime', 'slug')
        field_classes = {
            'updated': SplitDateTimeField,
            'publication_datetime': SplitDateTimeField,
        }
        widgets = {
            'subject': forms.TextInput(),
            'intro': forms.Textarea(),
            'text': forms.Textarea(),
            'publication_datetime': NativeSplitDateTimeWidget(),
            'updated': NativeSplitDateTimeWidget(),
        }


class EditPublicArticleForm(EditArticleForm):

    class Meta(EditArticleForm.Meta):
        exclude = ['slug', 'publication_datetime']


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
        convert = lambda v: v.replace(tzinfo=get_current_timezone())
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
            'date': NativeDateInput,
            'time': NativeTimeInput,
            'enddate': NativeDateInput,
            'endtime': NativeTimeInput,
        }
        exclude = ['author', 'slug', 'visible']


class EditEventForm(NewEventForm):
    visible = forms.BooleanField(label=gettext_lazy('Display event?'),
                required=False)

    class Meta(NewEventForm.Meta):
        exclude = ['author', 'slug']
