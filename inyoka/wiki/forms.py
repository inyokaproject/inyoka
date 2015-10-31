# -*- coding: utf-8 -*-
"""
    inyoka.wiki.forms
    ~~~~~~~~~~~~~~~~~

    Contains all the forms we use in the wiki.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django import forms
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils.functional import allow_lazy

from inyoka.forum.models import Topic
from inyoka.markup import parse, StackExhaused
from inyoka.utils.forms import UserField, DateWidget
from inyoka.utils.sessions import SurgeProtectionMixin
from inyoka.utils.storage import storage
from inyoka.utils.text import join_pagename, normalize_pagename
from inyoka.utils.urls import href
from inyoka.wiki.acl import has_privilege, test_changes_allowed
from inyoka.wiki.models import Page
from inyoka.wiki.utils import has_conflicts


class NewArticleForm(SurgeProtectionMixin, forms.Form):
    """Form for creating new wiki articles."""
    name = forms.CharField(widget=forms.TextInput(), required=True,
                           label=_(u'The title of the article you want to '
                                   u'create.'))
    template = forms.ChoiceField(required=False,
                                 label=_(u'The template that this new article '
                                         u'should be using.'))

    def __init__(self, user=None, reserved_names=[], template_choices=[],
                 data=None):
        """Initialize the form.

        Takes the user object of the current request, a list of reserved names
        that are not allowed as article names and a list of available templates
        to fill the ChoicesField.
        """
        self.user = user
        self.reserved_names = reserved_names

        super(NewArticleForm, self).__init__(data)
        self.fields['template'].choices = template_choices

    def clean_name(self):
        """Make sure page does not exist and user has privilege to create."""
        name = normalize_pagename(self.cleaned_data['name'])

        # If user has no right to create the article, alter the name to include
        # the "construction" prefix.
        if not has_privilege(self.user, name, 'create'):
            name = join_pagename(storage['wiki_construction_area'], name)
            # See if the user now has the right to create this page.
            if not has_privilege(self.user, name, 'create'):
                # This could mean that the page exists and was previously marked
                # as deleted.
                raise forms.ValidationError(_(u'You do not have permission to '
                                              u'create this page.'),
                                            code='requires_privilege')

        # make sure the name does not conflict with basic wiki views, such as
        # create, edit, last_changes etc.
        if name in self.reserved_names:
                raise forms.ValidationError(_(u'You can not create a page '
                                              u'with a reserved name.'),
                                            code='reserved_name')

        # See if the page already exists.
        # TODO: we should probably just redirect to the edit form in this case.
        if Page.objects.filter(name=name).exists():
            raise forms.ValidationError(_(u'The page %(name)s already exists.'),
                                        code='page_exists',
                                        params={'name': name})
        return name

    def clean_template(self):
        """Make sure user can access the chosen template."""
        template = self.cleaned_data['template']

        if not has_privilege(self.user, template, 'read'):
            # Honestly, this should never happen.
            raise forms.ValidationError(_(u'You do not have permission to read '
                                          u'this template.'),
                                        code='require_read_privilege')
        return template


class PageEditForm(SurgeProtectionMixin, forms.Form):
    """
    Used in the `do_edit` action for existing pages.  The following fields are
    available:

    `text`
        The text of the page as textarea.

    `note`
        A textfield for the change note.
    """
    text = forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 50}))
    note = forms.CharField(max_length=512, required=True,
                           widget=forms.TextInput(attrs={'size': 50}),
                           help_text=storage.get_lazy('wiki_edit_note_rendered'))

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
        help_text=ugettext_lazy(u'You can find the slug of a topic in the URL '
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
