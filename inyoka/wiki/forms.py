"""
    inyoka.wiki.forms
    ~~~~~~~~~~~~~~~~~

    Contains all the forms we use in the wiki.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from django import forms
from django.utils import timezone as dj_timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from inyoka.markup.base import StackExhaused, parse
from inyoka.utils.diff3 import merge
from inyoka.utils.forms import DateWidget, TopicField, UserField
from inyoka.utils.sessions import SurgeProtectionMixin
from inyoka.utils.storage import storage
from inyoka.utils.text import join_pagename, normalize_pagename
from inyoka.wiki.acl import has_privilege, test_changes_allowed
from inyoka.wiki.models import Page
from inyoka.wiki.utils import has_conflicts


class NewArticleForm(SurgeProtectionMixin, forms.Form):
    """Form for creating new wiki articles."""
    name = forms.CharField(widget=forms.TextInput(), required=True,
                           label=gettext_lazy('The title of the article you want to '
                                   'create.'))
    template = forms.ChoiceField(required=False,
                                 label=gettext_lazy('The template that this new article '
                                         'should be using.'))

    def __init__(self, user=None, reserved_names=[], template_choices=[],
                 data=None):
        """Initialize the form.

        Takes the user object of the current request, a list of reserved names
        that are not allowed as article names and a list of available templates
        to fill the ChoicesField.
        """
        self.user = user
        self.reserved_names = reserved_names

        super().__init__(data)
        self.fields['template'].choices = template_choices

        if self.user.is_team_member:
            self.surge_protection_timeout = None

    def clean_name(self):
        """Make sure page does not exist and user has privilege to create."""
        name = normalize_pagename(self.cleaned_data['name'])

        # If user has no right to create the article, alter the name to include
        # the "construction" prefix.
        if not has_privilege(self.user, name, 'create'):
            name = join_pagename(storage['wiki_newpage_root'], './' + name)
            # See if the user now has the right to create this page.
            if not has_privilege(self.user, name, 'create'):
                # This could mean that the page exists and was previously
                # marked as deleted.
                raise forms.ValidationError(_('You do not have permission to '
                                              'create this page.'),
                                            code='requires_privilege')

        # make sure the name does not conflict with basic wiki views, such as
        # create, edit, last_changes etc.
        if name in self.reserved_names:
                raise forms.ValidationError(_('You can not create a page '
                                              'with a reserved name.'),
                                            code='reserved_name')

        # See if the page already exists.
        if Page.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError(_('The page %(name)s already exists.'),
                                        code='page_exists',
                                        params={'name': name})
        return name

    def clean_template(self):
        """Make sure user can access the chosen template."""
        template = self.cleaned_data['template']

        if template == '':
            return None

        if not has_privilege(self.user, template, 'read'):
            # Honestly, this should never happen.
            raise forms.ValidationError(_('You do not have permission to read '
                                          'this template.'),
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

    `edit_time`:
        A DateTimeField for the time when the user started editing. This is used
        to determine if there are newer revisions and there may be an editing
        conflict.

    `revision`:
        The revision the user is basing the edit on. Not necessarily the latest
        revision.
    """
    text = forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 50}))
    note = forms.CharField(label=gettext_lazy('Edit summary'),
                           widget=forms.TextInput(attrs={'size': 50, 'spellcheck': 'true'}),
                           max_length=512, required=True,
                           help_text=storage['wiki_edit_note_rendered'])
    edit_time = forms.CharField(widget=forms.HiddenInput(), required=True)
    revision = forms.CharField(widget=forms.HiddenInput(), required=True)

    def __init__(self, user=None, name=None, revision=None, data=None):
        """Initialize the form.

        `user`:
            The user editing the page.

        `name`:
            The name of the page being edited.

        `data`:
            A dict containing the initial values for the fields.
        """
        super().__init__(data=data)
        self.user = user
        self.name = name
        revision = data['revision'] if data is not None else revision
        self.old_rev = Page.objects.get_by_name_and_rev(self.name,
                                                        revision).rev
        self.latest_rev = Page.objects.get_by_name(self.name).revisions.latest()

        if self.user.is_team_member:
            self.surge_protection_timeout = None

    def clean(self):
        """Test if we need to merge."""
        super().clean()

        data = self.data.copy()
        latest_change_time = self.latest_rev.change_date
        edit_time = datetime.strptime(data['edit_time'], '%Y-%m-%d %H:%M:%S.%f')

        if edit_time < latest_change_time:
            # The user started editing (edit_time) before the last change.
            data['text'] = merge(old=self.old_rev.text.value,
                                 other=self.latest_rev.text.value,
                                 new=data['text'])
            data['edit_time'] = dj_timezone.now()
            self.data = data
            self.add_error('text', _('Somebody else edited the page while you '
                                     'were making your changes. We tried to '
                                     'merge the text automatically. Please '
                                     'confirm that everything is ok.'))

    def clean_text(self):
        text = self.cleaned_data['text']

        if text == self.old_rev.text.value:
            raise forms.ValidationError(_('You have not made any changes.'),
                                        code='unchanged')

        try:
            tree = parse(text, catch_stack_errors=False)
        except StackExhaused:
            raise forms.ValidationError(_('The text contains too many nested '
                                          'elements.'),
                                        code='stack_exhausted')

        if has_conflicts(tree):
            raise forms.ValidationError(_('The text contains conflict markers.'),
                                        code='contains_conflicts')

        if not test_changes_allowed(self.user,
                                    self.name,
                                    self.old_rev.text.value,
                                    text):
            raise forms.ValidationError(_('You are not permitted to make '
                                          'this change.'),
                                        code='require_privilege')

        return text


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

    filename = forms.CharField(max_length=512, required=False,
                help_text=gettext_lazy('Rename the file after upload'))

    override = forms.BooleanField(label=gettext_lazy('Overwrite existing file with same name'),
                                  required=False)

    text = forms.CharField(label=gettext_lazy('Description of attachment'),
                           widget=forms.Textarea,
                           required=False)

    note = forms.CharField(label=gettext_lazy('Edit summary'), max_length=512, required=False)


class EditAttachmentForm(forms.Form):
    """
    A form for editing existing Attachments.  For a more detailed
    description, have a look at the AddAttachmentForm.
    """
    attachment = forms.FileField(required=False)
    text = forms.CharField(label=gettext_lazy('Description of attachment'),
                           widget=forms.Textarea,
                           required=False)
    note = forms.CharField(label=gettext_lazy('Edit summary'),
                           max_length=512, required=False)


class ManageDiscussionForm(forms.Form):
    """Let the user set an existing thread as discussion of a page"""
    topic = TopicField(required=False)


class MvBaustelleForm(forms.Form):
    """Move page to the "Baustelle"""
    new_name = forms.CharField(label=gettext_lazy('New page name'), required=True)
    user = UserField(label=gettext_lazy('Edited by'), required=True)
    completion_date = forms.DateField(label=gettext_lazy('Completion date'),
                                      required=False, widget=DateWidget,
                                      localize=True)
