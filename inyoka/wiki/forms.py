# -*- coding: utf-8 -*-
"""
    inyoka.wiki.forms
    ~~~~~~~~~~~~~~~~~

    Contains all the forms we use in the wiki.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django import forms
from django.utils.translation import ugettext_lazy, ugettext as _

from inyoka.markup import parse, StackExhaused
from inyoka.utils.forms import UserField, DateWidget
from inyoka.utils.sessions import SurgeProtectionMixin
from inyoka.utils.urls import href
from inyoka.forum.models import Topic
from inyoka.wiki.utils import has_conflicts
from inyoka.wiki.acl import test_changes_allowed


class PageEditForm(SurgeProtectionMixin, forms.Form):
    """
    Used in the `do_edit` action for both new and existing pages.  The
    following fields are available:

    `text`
        The text of the page as textarea.

    `note`
        A textfield for the change note.
    """
    text = forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 50}))
    note = forms.CharField(max_length=512, required=True,
                           widget=forms.TextInput(attrs={'size': 50}))

    def __init__(self, user=None, page_name=None, old_text=None, data=None):
        forms.Form.__init__(self, data)
        self.user = user
        self.page_name = page_name
        self.old_text = old_text

    def clean_text(self):
        if 'text' not in self.cleaned_data:
            return
        try:
            tree = parse(self.cleaned_data['text'], catch_stack_errors=False)
        except StackExhaused:
            raise forms.ValidationError(_(u'The text contains too many nested '
                                          u'elements.'))
        if has_conflicts(tree):
            raise forms.ValidationError(_(u'The text contains conflict markers'))
        elif self.user is not None and not \
             test_changes_allowed(self.user, self.page_name, self.old_text,
                                  self.cleaned_data['text']):
            raise forms.ValidationError(_(u'You are not permitted to make '
                                          u'this changes'))
                                       # Du hast Änderungen vorgenommen, '
                                       # u'die dir durch die Zugriffsrechte '
                                       # u'verwehrt werden.')
        return self.cleaned_data['text']


class AddAttachmentForm(forms.Form):
    """
    Allows the user to upload new attachments.  It's used in the `do_attach`
    action and provides the following fields:

    `attachment`
        A file field for the uploaded file.

    `filename`
        The target filename.  If this is left blank the original filename
        is used for the server too.

    `override`
        A checkbox for the override flag.  If this is true a filename with
        the same name is overridden (A new revision is created)

    `text`
        The description of the attachment as textarea.

    `note`
        A textfield for the change note.
    """
    attachment = forms.FileField(required=True)
    filename = forms.CharField(max_length=512, required=False)
    override = forms.BooleanField(required=False)
    text = forms.CharField(label=ugettext_lazy(u'Description'),
                           widget=forms.Textarea,
                           required=False)
    note = forms.CharField(max_length=512, required=False)


class EditAttachmentForm(forms.Form):
    """
    A form for editing existing Attachments.  For a more detailed
    description, have a look at the AddAttachmentForm.
    """
    attachment = forms.FileField(required=False)
    text = forms.CharField(label=ugettext_lazy(u'Description'),
                           widget=forms.Textarea,
                           required=False)
    note = forms.CharField(max_length=512, required=False)


class ManageDiscussionForm(forms.Form):
    """Let the user set an existing thread as discussion of a page"""
    topic = forms.CharField(label=_('Slug of the topic'), max_length=50,
        help_text= ugettext_lazy(u'You can find the slug of a topic in the URL '
            u'(e.g. <var>example</var> when <em>%(example)s</em>)') % {
                'example': href('forum', 'topic', 'example')},
            required=False)

    def clean_topic(self):
        d = self.cleaned_data
        if not d.get('topic'):
            return None
        try:
            topic = Topic.objects.get(slug=d['topic'])
        except Topic.DoesNotExist:
            raise forms.ValidationError(_(u'This topic does not exist.'))
        return topic


class MvBaustelleForm(forms.Form):
    """Move page to the "Baustelle"""
    new_name = forms.CharField(label=ugettext_lazy(u'New page name'), required=True)
    user = UserField(label=ugettext_lazy('Edited by'), required=True)
    completion_date = forms.DateField(label=ugettext_lazy(u'Completion date'),
                                      required=False, widget=DateWidget,
                                      localize=True)
