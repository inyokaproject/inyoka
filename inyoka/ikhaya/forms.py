"""
    inyoka.ikhaya.forms
    ~~~~~~~~~~~~~~~~~~~

    Forms for the Ikhaya.

    :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from django import forms
from django.forms import SplitDateTimeField
from django.utils import timezone as dj_timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from inyoka.ikhaya.models import Article, Category, Event, Suggestion
from inyoka.portal.models import StaticFile
from inyoka.utils.forms import (
    NativeSplitDateTimeWidget,
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
            if instance.public and not instance.updated:
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

            q = Article.objects.annotate_publication_date_utc()
            q = q.filter(slug=slug, publication_date_utc=pub_datetime)

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

    def save(self, user):
        event = super().save(commit=False)

        event.author = user
        event.save()

        return event

    def clean(self):
        super().clean()

        cleaned_data = self.cleaned_data

        if cleaned_data.get('end') and cleaned_data.get('start') and cleaned_data['end'] <= cleaned_data['start']:
            self.add_error('end', _('The end date must occur after the start date.'))

        if cleaned_data['location_lat'] and not cleaned_data['location_long']:
            self.add_error('location_long', _('You must specify a location longitude.'))

        if not cleaned_data['location_lat'] and cleaned_data['location_long']:
            self.add_error('location_lat', _('You must specify a location latitude.'))

        return cleaned_data

    class Meta:
        model = Event
        field_classes = {
            'start': SplitDateTimeField,
            'end': SplitDateTimeField,
        }
        widgets = {
            'start': NativeSplitDateTimeWidget(),
            'end': NativeSplitDateTimeWidget(),
        }
        exclude = ['author', 'slug', 'visible']


class EditEventForm(NewEventForm):

    class Meta(NewEventForm.Meta):
        exclude = ['author', 'slug']
