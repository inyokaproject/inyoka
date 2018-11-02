# -*- coding: utf-8 -*-
"""
    inyoka.forum.forms
    ~~~~~~~~~~~~~~~~~~

    Forms for the forum.

    :copyright: (c) 2007-2018 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import urllib
import urlparse

from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy

from inyoka.forum.constants import get_distro_choices, get_version_choices
from inyoka.forum.models import Forum, Topic
from inyoka.utils.forms import MultiField, StrippedCharField
from inyoka.utils.local import current_request
from inyoka.utils.sessions import SurgeProtectionMixin
from inyoka.utils.spam import check_form_field
from inyoka.utils.text import slugify


class ForumField(forms.ChoiceField):
    def refresh(self, priv='forum.view_forum', add=[], remove=[]):
        """
        Generates a hierarchical representation of all forums for a choice field.
        Only forums with at least `priv` for the current user are taken into
        account. Addtitional items can be prepanded as a list of tuples
        `[(val1,repr1),(val2,repr2)]` with the `add` keyword. To remove items
        from the list use a list of Forum objects in the `remove` keyword.

        Optgroups are used to disable categories in the choice field.
        """
        forums = Forum.objects.get_forums_filtered(current_request.user,
            priv, sort=True)

        for f in remove:
            if f in forums:
                forums.remove(f)

        forums = Forum.get_children_recursive(forums)
        choices = []
        for offset, f in forums:
            if f.is_category:
                choices.append((f.name, []))
            else:
                title = f.name[0] + u' ' + (u'   ' * offset) + f.name
                choices[-1][1].append((f.id, title))
        self.choices = add + choices


class EditPostForm(SurgeProtectionMixin, forms.Form):
    """
    Allows the user to edit the text of a post.
    This form takes the additional keyword argument `is_first_post`.
    It's generally used together with `AddAttachmentForm`.
    """
    text = StrippedCharField(widget=forms.Textarea)
    # the following fields only appear if the post is the first post of the
    # topic.
    #: the user can select, whether the post's topic should be sticky or not.
    sticky = forms.BooleanField(required=False)
    title = forms.CharField(widget=forms.TextInput(attrs={'size': 60}), max_length=100)
    ubuntu_version = forms.ChoiceField(required=False)
    ubuntu_distro = forms.ChoiceField(required=False)

    surge_protection_timeout = settings.FORUM_SURGE_PROTECTION_TIMEOUT

    def __init__(self, is_first_post, needs_spam_check, request, *args, **kwargs):
        self.needs_spam_check = needs_spam_check
        self.request = request
        super(EditPostForm, self).__init__(*args, **kwargs)
        self.fields['ubuntu_version'].choices = get_version_choices()
        self.fields['ubuntu_distro'].choices = get_distro_choices()
        if not is_first_post:
            for k in ['sticky', 'title', 'ubuntu_version', 'ubuntu_distro']:
                del self.fields[k]

    def clean_text(self):
        if 'send' in self.data:
            return check_form_field(self, 'text', self.needs_spam_check, self.request, 'forum-post')


class NewTopicForm(SurgeProtectionMixin, forms.Form):
    """
    Allows the user to create a new topic. It provides the following fields:

    `title`
        The title of the topic.

    `text`
        The text of the first post inside the topic.

    `polls`
        A list of new polls bound to this topic.

    `ubuntu_version`
        The ubuntu version the user has.

    `ubuntu_distro`
        The ubuntu distribution the user has.

    It's used together with `AddAttachmentForm` in general.
    """
    title = StrippedCharField(widget=forms.TextInput(attrs={'size': 60}),
                            max_length=100)
    text = StrippedCharField(widget=forms.Textarea)
    ubuntu_version = forms.ChoiceField(required=False)
    ubuntu_distro = forms.ChoiceField(required=False)
    sticky = forms.BooleanField(required=False)

    surge_protection_timeout = settings.FORUM_SURGE_PROTECTION_TIMEOUT

    def __init__(self, force_version, needs_spam_check, request, *args, **kwargs):
        self.force_version = force_version
        self.needs_spam_check = needs_spam_check
        self.request = request
        super(NewTopicForm, self).__init__(*args, **kwargs)
        self.fields['ubuntu_version'].choices = get_version_choices()
        self.fields['ubuntu_distro'].choices = get_distro_choices()

    def clean_ubuntu_version(self):
        ubuntu_version = self.cleaned_data.get('ubuntu_version', None)
        if self.force_version and not ubuntu_version:
            raise forms.ValidationError(forms.fields.Field.
                                        default_error_messages['required'])
        return ubuntu_version

    def clean_ubuntu_distro(self):
        ubuntu_distro = self.cleaned_data.get('ubuntu_distro', None)
        if self.force_version and not ubuntu_distro:
            raise forms.ValidationError(forms.fields.Field.
                                        default_error_messages['required'])
        return ubuntu_distro

    def clean_text(self):
        if 'send' in self.data:
            return check_form_field(self, 'text', self.needs_spam_check, self.request, 'forum-post')


class MoveTopicForm(forms.Form):
    """
    This form gives the user the possibility to select a new forum for a
    topic.
    """
    forum = ForumField()
    edit_post = forms.BooleanField(required=False, label=_('Edit first post afterwards'))


class SplitTopicForm(forms.Form):
    """
    This form used on the split topic page gives the user the choice whether
    the posts should be moved into an existing or a new topic.
    """
    action = forms.ChoiceField(choices=(('add', ''), ('new', '')))
    #: the title of the new topic
    title = forms.CharField(max_length=200)
    #: the forum of the new topic
    forum = ForumField()
    #: the slug of the existing topic
    topic = forms.CharField(max_length=200)
    #: version info. defaults to the values set in the old topic.
    ubuntu_version = forms.ChoiceField(required=False)
    ubuntu_distro = forms.ChoiceField(required=False)
    edit_post = forms.BooleanField(required=False, label=_('Edit first post afterwards'))

    def __init__(self, *args, **kwargs):
        super(SplitTopicForm, self).__init__(*args, **kwargs)
        self.fields['ubuntu_version'].choices = get_version_choices()
        self.fields['ubuntu_distro'].choices = get_distro_choices()

    def clean(self):
        data = self.cleaned_data
        if data.get('action') == 'new':
            self._errors.pop('topic', None)
        elif data.get('action') == 'add':
            self._errors.pop('title', None)
            self._errors.pop('forum', None)
        return data

    def clean_topic(self):
        slug = self.cleaned_data.get('topic')
        if slug:
            # Allow URL based Slugs
            try:
                slug = urlparse.urlparse(slug)[2].split('/')[2]
            except IndexError:
                slug = urllib.unquote(slug)

            try:
                topic = Topic.objects.get(slug=slug)
            except Topic.DoesNotExist:
                raise forms.ValidationError(_(u'No topic with this '
                                              u'slug found.'))
            return topic
        return slug

    def clean_forum(self):
        id = self.cleaned_data.get('forum')
        forum = Forum.objects.get(id=int(id))
        if forum.is_category:
            raise forms.ValidationError(_(u'You cannot move a topic into a '
                                          u'category. Please choose a forum.'))
        return forum


class AddAttachmentForm(forms.Form):
    """
    Allows the user to upload new attachments.  It provides the following fields:

    `attachment`
        A file field for the uploaded file.

    `filename`
        The target filename.  If this is left blank the original filename
        is used for the server too.

    `override`
        A checkbox for the override flag.  If this is true a filename with
        the same name is overridden (A new revision is created)

    `description`
        The description of the attachment as textarea.
    """
    attachment = forms.FileField(required=True)
    filename = forms.CharField(max_length=512, required=False)
    override = forms.BooleanField(required=False)
    comment = forms.CharField(label=ugettext_lazy(u'Description'), required=False,
                  widget=forms.TextInput(attrs={'size': '60'}))


class AddPollForm(forms.Form):
    question = forms.CharField(max_length=250, widget=forms.TextInput(attrs={'size': '60'}))
    multiple = forms.BooleanField(required=False)
    options = MultiField((forms.CharField(max_length=250, widget=forms.TextInput(attrs={'size': '50'})),))
    duration = forms.IntegerField(min_value=1, max_value=3650, required=False,
                                  widget=forms.TextInput(attrs={'size': '3'}))


class ReportTopicForm(forms.Form):
    """
    Allows the user to report the moderators a topic.
    It's only field is a text field where the user can write why he thinks
    that the moderators should have a look at this topic.
    """
    text = forms.CharField(label=ugettext_lazy(u'Reason'), widget=forms.Textarea)


class ReportListForm(forms.Form):
    """
    This form lets the moderator select a bunch of topics for removing the
    reported flag.
    """
    selected = forms.MultipleChoiceField()


class EditForumForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = [
            'name',
            'slug',
            'description',
            'parent',
            'position',
            'newtopic_default_text',
            'force_version',
            'user_count_posts',
            'support_group',
            'welcome_title',
            'welcome_text']

    def clean_welcome_title(self):
        data = self.cleaned_data
        if data.get('welcome_text') and not data.get('welcome_title'):
            raise forms.ValidationError(ugettext_lazy(u'You must enter a title '
                u'in order to set the welcome message'))
        return data['welcome_title']

    def clean_welcome_msg_text(self):
        data = self.cleaned_data
        if data.get('welcome_title') and not data.get('welcome_text'):
            raise forms.ValidationError(ugettext_lazy(u'You must enter a text '
                u'in order to set the welcome message'))
        return data['welcome_text']

    def clean_slug(self):
        data = slugify(self.cleaned_data['slug'])
        if data == 'new':
            raise forms.ValidationError(ugettext_lazy(u'“new” is not a valid forum slug'))
        return data
