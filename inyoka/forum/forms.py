# -*- coding: utf-8 -*-
"""
    inyoka.forum.forms
    ~~~~~~~~~~~~~~~~~~

    Forms for the forum.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django import forms
from inyoka.utils.forms import MultiField, SlugField, StrippedCharField
from inyoka.utils.html import escape
from inyoka.forum.models import Topic, Forum
from inyoka.forum.constants import VERSION_CHOICES, DISTRO_CHOICES
from inyoka.utils.sessions import SurgeProtectionMixin


class NewPostForm(SurgeProtectionMixin, forms.Form):
    """
    Allows the user to create a new post.  It provides the following fields:
    `text`
        The text for the post.
    It's generally used together with `AddAttachmentForm`.
    """
    text = StrippedCharField(widget=forms.Textarea)


class EditPostForm(forms.Form):
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
    title = forms.CharField(widget=forms.TextInput(attrs={'size':60}))
    ubuntu_version = forms.ChoiceField(choices=VERSION_CHOICES,
                                                required=False)
    ubuntu_distro = forms.ChoiceField(choices=DISTRO_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        self.is_first_post = kwargs.pop('is_first_post', False)
        forms.Form.__init__(self, *args, **kwargs)

    def clean(self):
        data = self.cleaned_data
        if not self.is_first_post:
            for k in ['sticky', 'title', 'ubuntu_version', 'ubuntu_distro']:
                self._errors.pop(k, None)
        return data


class NewTopicForm(SurgeProtectionMixin, forms.Form):
    """
    Allows the user to create a new topic.
    It provides the following fields:
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
    title = StrippedCharField(widget=forms.TextInput(attrs={'size':60}),
                            max_length=100)
    text = StrippedCharField(widget=forms.Textarea)
    ubuntu_version = forms.ChoiceField(choices=VERSION_CHOICES,
                                                required=False)
    ubuntu_distro = forms.ChoiceField(choices=DISTRO_CHOICES, required=False)
    sticky = forms.BooleanField(required=False)

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

    def __init__(self, *args, **kwargs):
        self.force_version = kwargs.pop('force_version', False)
        forms.Form.__init__(self, *args, **kwargs)


class MoveTopicForm(forms.Form):
    """
    This form gives the user the possibility to select a new forum for a
    topic.
    """
    forum_id = forms.ChoiceField(widget=forms.Select(attrs=
        {'class':'firstletterselect'}))


class SplitTopicForm(forms.Form):
    """
    This form used on the split topic page gives the user the choice whether
    the posts should be moved into an existing or a new topic.
    """
    action = forms.ChoiceField(choices=(('add', ''), ('new', '')))
    #: the title of the new topic
    title = forms.CharField(max_length=200)
    #: the forum of the new topic
    forum = forms.ChoiceField()
    #: the slug of the existing topic
    topic = forms.CharField(max_length=200)
    #: version info. defaults to the values set in the old topic.
    ubuntu_version = forms.ChoiceField(choices=VERSION_CHOICES,
                                                required=False)
    ubuntu_distro = forms.ChoiceField(choices=DISTRO_CHOICES, required=False)

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
            if slug.startswith(u'http://'):
                slug = slug.strip(u'/').split(u'/')[-1]
            try:
                topic = Topic.objects.get(slug=slug)
            except Topic.DoesNotExist:
                raise forms.ValidationError(u'Ein Thema mit diesem Slug '
                                            u'existiert nicht')
            return topic
        return slug

    def clean_forum(self):
        id = self.cleaned_data.get('forum')
        return Forum.objects.get(id=int(id))


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
    comment = forms.CharField(label='Beschreibung', required=False,
                  widget=forms.TextInput(attrs={'size':'60'}))


class AddPollForm(forms.Form):
    question = forms.CharField(max_length=250, widget=forms.TextInput(attrs={'size':'60'}))
    multiple = forms.BooleanField(required=False)
    options = MultiField((forms.CharField(max_length=250, widget=forms.TextInput(attrs={'size':'50'})),))
    duration = forms.IntegerField(min_value=1, max_value=3650, required=False,
                                  widget=forms.TextInput(attrs={'size':'3'}))


class ReportTopicForm(forms.Form):
    """
    Allows the user to report the moderators a topic.
    It's only field is a text field where the user can write why he thinks
    that the moderators should have a look at this topic.
    """
    text = forms.CharField(label='Begründung', widget=forms.Textarea)


class ReportListForm(forms.Form):
    """
    This form lets the moderator select a bunch of topics for removing the
    reported flag.
    """
    selected = forms.MultipleChoiceField()

class EditForumForm(forms.Form):
    name = forms.CharField(label=u'Name', max_length=100)
    slug = SlugField(label=u'Slug', max_length=100, required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}),
                                  label=u'Beschreibung', required=False)
    parent = forms.ChoiceField(label=u'Elternforum', required=False)
    position = forms.IntegerField(label=u'Position', initial=0)

    welcome_msg_subject = forms.CharField(label=u'Titel', max_length=120,
        required=False)
    welcome_msg_text = forms.CharField(label=u'Text', required=False,
                                       widget=forms.Textarea(attrs={'rows': 3}))
    newtopic_default_text = forms.CharField(label=u'Standardtext für neue Themen',
                                            widget=forms.Textarea(attrs={'rows': 3}),
                                            required=False)
    force_version = forms.BooleanField(label=u'Angabe der Ubuntu-Version erzwingen',
                                       required=False)
    count_posts = forms.BooleanField(label=u'Beiträge in diesem Forum werden gezählt',
        help_text=u'Dieser Wert ist nur über das Webteam veränderbar',
        required=False, widget=forms.CheckboxInput({'readonly': True}))

    def __init__(self, *args, **kwargs):
        self.forum = kwargs.pop('forum', None)
        super(EditForumForm, self).__init__(*args, **kwargs)

    def clean_welcome_msg_subject(self):
        data = self.cleaned_data
        if data.get('welcome_msg_text') and not data.get('welcome_msg_subject'):
            raise forms.ValidationError(u'Du musst einen Titel angeben für die'
                u' Willkommensnachricht')
        return data['welcome_msg_subject']

    def clean_welcome_msg_text(self):
        data = self.cleaned_data
        if data.get('welcome_msg_subject') and not data.get('welcome_msg_text'):
            raise forms.ValidationError(u'Du musst einen Text für die '
                u'Willkommensnachricht eingeben.')
        return data['welcome_msg_text']

    def clean_slug(self):
        data = self.cleaned_data['slug']
        if data == 'new':
            raise forms.ValidationError(u"new is not a valid forum slug")

        slug = self.forum.slug if self.forum else ''
        if data != slug and Forum.objects.filter(slug=data).exists():
            raise forms.ValidationError(u"Bitte einen anderen Slug angeben, „%s“ ist schon "
                     u"vergeben." % escape(data))
        return data
