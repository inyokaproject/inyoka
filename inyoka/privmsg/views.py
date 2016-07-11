# -*- coding: utf-8 -*-
"""
    inyoka.privmsg.views
    ~~~~~~~~~~~~~~~~~~~~

    Views for private messages between users.

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse_lazy
from django.http import Http404, HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, View
from django.views.generic.edit import FormMixin, FormView
from django.views.generic.list import ListView
from inyoka.forum.models import Topic
from inyoka.ikhaya.models import Suggestion
from inyoka.portal.user import User
from inyoka.privmsg.forms import (
    MessageComposeForm,
    MultiMessageSelectForm,
    PrivilegedMessageComposeForm,
)
from inyoka.privmsg.models import MessageData
from inyoka.utils.django_19_auth_mixins import LoginRequiredMixin
from inyoka.utils.flash_confirmation import ConfirmActionMixin
from inyoka.utils.forms import FormPreviewMixin
from inyoka.utils.views import PermissionRequiredMixin
from inyoka.wiki.utils import quote_text

MESSAGES_PER_PAGE = 20


# "Folder" level views
# --------------------
class MessagesFolderView(LoginRequiredMixin, ListView):
    """Base View to Show a list of private messages for a user."""

    template_name = 'privmsg/folder.html'
    context_object_name = 'messages'
    paginate_by = MESSAGES_PER_PAGE
    queryset_name = None
    folder = None
    folder_name = None

    def get_queryset(self):
        """Return the queryset."""
        if self.queryset_name is not None:
            # basically, take the `queryset_name` string and call it as a method
            # on the current users `message_set`.
            queryset = getattr(self.request.user.message_set, self.queryset_name)
            return queryset().optimized()
        else:
            raise ImproperlyConfigured(
                '{0} is missing the queryset_name attribute. Define {0}.queryset_name '
                'or overwrite {0}.get_queryset().'.format(self.__class__.__name__)
            )


class InboxedMessagesView(MessagesFolderView):
    """Show the list of messages that are in the inbox (i.e. not archived)."""

    queryset_name = 'inboxed'
    folder = 'inbox'
    folder_name = _(u'Inbox')


class SentMessagesView(MessagesFolderView):
    """Show the list of messages that the user sent himself."""

    queryset_name = 'sent'
    folder = 'sent'
    folder_name = _(u'Sent')


class ArchivedMessagesView(MessagesFolderView):
    """Show the list of messages that are in the archive."""

    queryset_name = 'archived'
    folder = 'archive'
    folder_name = _(u'Archive')


class TrashedMessagesView(MessagesFolderView):
    """Show the list of messages that are in the trash."""

    queryset_name = 'trashed'
    folder = 'trash'
    folder_name = _(u'Trash')


class ReadMessagesView(MessagesFolderView):
    """Show the list of messages that were read."""

    queryset_name = 'read'
    folder = 'read'
    folder_name = _(u'Read')


class UnreadMessagesView(MessagesFolderView):
    """Show the list of messages that are unread."""

    queryset_name = 'unread'
    folder = 'unread'
    folder_name = _(u'Unread')


# Message level views
# -------------------
class MessageView(LoginRequiredMixin, DetailView):
    """Display a message."""

    context_object_name = 'message'
    template_name = 'privmsg/message.html'

    def get_queryset(self):
        """Return the queryset of this users messages and make sure it is optimized()."""
        return self.request.user.message_set.optimized()

    def get_object(self, queryset=None):
        """When retrieving the object by pk, make sure it is marked as read."""
        message = super(MessageView, self).get_object(queryset)
        message.mark_read()
        return message


class MessageToArchiveView(ConfirmActionMixin, MessageView):
    """Move message to the archive."""

    confirm_message = _(u'Do you want to archive this message?')
    success_message = _(u'The message was archived.')
    confirm_label = _(u'Archive')
    success_url = reverse_lazy('privmsg-archive')

    def confirm_action(self):
        """Archive the message, when the flash confirmation action succeeds."""
        self.object.archive()


class MessageToTrashView(ConfirmActionMixin, MessageView):
    """Move message to trash."""

    confirm_message = _(u'Do you want to move this message to trash?')
    success_message = _(u'The message was moved to trash.')
    confirm_label = _(u'Trash')
    success_url = reverse_lazy('privmsg-trash')

    def confirm_action(self):
        """Archive the message, when the flash confirmation action succeeds."""
        self.object.trash()


class MessageRestoreView(ConfirmActionMixin, MessageView):
    """Restore message from `trash` or `archive` to `inbox` or `sent`."""

    confirm_message = _(u'Do you want to restore this message?')
    success_message = _(u'The message has been restored.')
    confirm_label = _(u'Restore')

    def confirm_action(self):
        """Restore the message, when the flash confirmation action succeeds."""
        self.object.restore()

    def get_success_url(self):
        """Get the redirection URL for a successfully restored message."""
        return self.object.get_absolute_url(action='folder')


class MessageDeleteView(ConfirmActionMixin, MessageView):
    """Delete a message."""

    confirm_message = _(u'Do you want to delete this message? You will not be able to recover it!')
    success_message = _(u'The message was deleted.')
    confirm_label = _(u'Delete')
    success_url = reverse_lazy('privmsg-inbox')

    def confirm_action(self):
        """Delete the message, when the action is confirmed."""
        self.object.delete()


# Composing messages
# ------------------
class BaseMessageComposeView(LoginRequiredMixin, FormPreviewMixin, FormView):
    """Base class for the compose views."""
    template_name = 'privmsg/compose.html'
    success_url = reverse_lazy('privmsg-sent')
    preview_fields = ['text']
    pk_url_kwarg = 'pk'
    slug_url_kwarg = 'slug'

    def get_form_class(self):
        """Get the form class based on user permission."""
        if self.request.user.can('send_group_pm'):
            return PrivilegedMessageComposeForm
        else:
            return MessageComposeForm

    def get_form_kwargs(self):
        """Make sure the form is called with the `user` argument."""
        kwargs = super(BaseMessageComposeView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Commit the message to the database."""
        MessageData.send(
            author=self.request.user,
            recipients=form.cleaned_data['recipients'],
            subject=form.cleaned_data['subject'],
            text=form.cleaned_data['text'],
        )
        messages.success(self.request, _(u'Your message has been sent.'))
        return HttpResponseRedirect(self.success_url)

    def preview_method(self, text):
        """Render the preview, see `FormPreviewMixin`."""
        return MessageData.get_text_rendered(text)

    def get_initial(self):
        """Return the `inital` data for the form."""
        self.object = self.get_object()
        return {
            'recipients': self.get_recipients(),
            'subject': self.get_subject(),
            'text': self.get_text(),
        }

    def get_object(self):
        """Returns an object. This is a dummy, overwrite in derived views."""
        return None

    def get_recipients(self):
        """Return a string of recipients. This is a dummy, overwrite in derived views."""
        return ''

    def get_subject(self):
        """Return the subject as a string. This is a dummy, overwrite in derived views."""
        return ''

    def get_text(self):
        """Return the message text as a string. This is a dummy, overwrite in derived views."""
        return ''


class MessageComposeView(BaseMessageComposeView):
    """View to compose private messages."""

    def get_recipients(self):
        """Provide the initial recipient for the form."""
        user = self.kwargs.get('user', None)
        return user if user is not None else ''


class MessageForwardView(BaseMessageComposeView):
    """Forward a private message"""

    def get_queryset(self):
        """Return the QuerySet of messages this user has access to."""
        return self.request.user.message_set.optimized()

    def get_object(self):
        """Return the message that is being forwarded."""
        pk = self.kwargs.get(self.pk_url_kwarg)
        return self.get_queryset().get(pk=pk)

    def get_subject(self):
        """Make sure the subject of the message starts with 'Fw: '."""
        if self.object.subject.lower().startswith('fw:'):
            return self.object.subject
        else:
            return u'Fw: {subject}'.format(subject=self.object.subject)

    def get_text(self):
        """Return the text of the forwarded message and make sure it's properly quoted."""
        return quote_text(text=self.object.text, author=self.object.author)


class MessageReplyView(BaseMessageComposeView):
    """Reply to a private message."""

    reply_to_all = False

    def get_queryset(self):
        """Return the QuerySet of messages this user has access to."""
        return self.request.user.message_set.optimized()

    def get_object(self):
        """Return the message that is being replied to."""
        pk = self.kwargs.get(self.pk_url_kwarg)
        return self.get_queryset().get(pk=pk)

    def get_recipients(self):
        """Return the list of usernames of recipients."""
        recipients = set([self.object.author])
        if self.reply_to_all:
            recipients.update(self.object.recipients)
        recipients.discard(self.request.user)
        recipients = ';'.join(r.username for r in recipients)
        return recipients

    def get_subject(self):
        """Make sure the subject of the message starts with 'Re: '."""
        if self.object.subject.lower().startswith('re:'):
            return self.object.subject
        else:
            return u'Re: {subject}'.format(subject=self.object.subject)

    def get_text(self):
        """Return text for the new message by quoting the old message."""
        return quote_text(text=self.object.text, author=self.object.author)


class MessageReplyReportedTopicView(PermissionRequiredMixin, BaseMessageComposeView):
    """Reply to reported topics on the forum."""

    model = Topic
    permission_required = 'manage_topics'

    def get_object(self):
        """Return the reported topic."""
        slug = self.kwargs.get(self.slug_url_kwarg)
        return Topic.objects.get(slug=slug)

    def get_recipients(self):
        """Return the list of recipients usernames for the form."""
        return User.objects.get(id=self.object.reporter_id).username

    def get_subject(self):
        """Return the subject of the reported topic and prefix it with 'Re:'."""
        return u'Re: {subject}'.format(subject=self.object.title)

    def get_text(self):
        """Return the quoted text of the report that is being answered."""
        return quote_text(text=self.object.reported, author=self.object.author)


class MessageReplySuggestedArticleView(PermissionRequiredMixin, BaseMessageComposeView):
    """Reply to suggested articles."""
    model = Suggestion
    permission_required = 'article_edit'

    def get_object(self):
        """Return the suggestion that is being replied to."""
        pk = self.kwargs.get(self.pk_url_kwarg)
        return Suggestion.objects.get(pk=pk)

    def get_recipients(self):
        """Return the list of recipients usernames for the form."""
        return self.object.author.username

    def get_subject(self):
        """Return the subject of the suggestion and prefix it with 'Re:'."""
        return u'Re: {subject}'.format(subject=self.object.title)

    def get_text(self):
        """Return the quoted text of the suggestion."""
        text = u'{}\n\n{}'.format(self.object.intro, self.object.text)
        return quote_text(text=text, author=self.object.author)


class MultiMessageProcessView(LoginRequiredMixin, FormMixin, View):
    """View to process forms and move multiple selected messages to a different folder."""

    form_class = MultiMessageSelectForm

    def get_form_kwargs(self):
        """Provide the form with the queryset for valid choices."""
        kwargs = super(MultiMessageProcessView, self).get_form_kwargs()
        kwargs['queryset'] = self.get_queryset()
        return kwargs

    def get_queryset(self):
        """The queryset containing the messages this user can access."""
        return self.request.user.message_set

    def post(self, request):
        """Respond to HTTP POST requests."""
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            # User gave invalid input, this might be a manipulation attempt
            raise Http404()

    def form_valid(self, form):
        """Process the filtered queryset."""
        queryset = form.cleaned_data['selected_messages']
        action = form.cleaned_data['action']

        if action == u'archive':
            queryset.bulk_archive()
            self.request.user.privmsg_count.db_count(write_cache=True)
            return HttpResponseRedirect(reverse_lazy('privmsg-archive'))

        elif action == u'trash':
            queryset.bulk_trash()
            self.request.user.privmsg_count.db_count(write_cache=True)
            return HttpResponseRedirect(reverse_lazy('privmsg-trash'))

        else:  # action == u'restore':
            queryset.bulk_restore()
            return HttpResponseRedirect(reverse_lazy('privmsg-inbox'))
