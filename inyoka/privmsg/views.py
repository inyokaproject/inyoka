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
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.generic import DetailView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView, MultipleObjectMixin
from inyoka.forum.acl import CAN_MODERATE, have_privilege
from inyoka.forum.models import Topic
from inyoka.ikhaya.models import Suggestion
from inyoka.portal.user import User
from inyoka.privmsg.forms import (
    MessageComposeForm,
    PrivilegedMessageComposeForm,
)
from inyoka.privmsg.models import Message, MessageData
from inyoka.utils.django_19_auth_mixins import LoginRequiredMixin
from inyoka.utils.flash_confirmation import ConfirmActionMixin
from inyoka.wiki.utils import quote_text

MESSAGES_PER_PAGE = 20


# "Folder" level views
# --------------------
class MessagesFolderView(LoginRequiredMixin, ListView, MultipleObjectMixin):
    """
    Base View to Show a list of private messages for a user.
    """
    template_name = 'privmsg/folder.html'
    context_object_name = 'messages'
    paginate_by = MESSAGES_PER_PAGE
    queryset_name = None
    folder = None
    folder_name = None

    def get_queryset(self):
        """
        Return the queryset.
        """
        if self.queryset_name is not None:
            # basically, take the `queryset_name` string and call it as a method
            # on the current users `message_set`
            q = getattr(self.request.user.message_set, self.queryset_name)
            return q().include_related()
        else:
            # Let other classes deal with the exception, if any.
            return super(MessagesFolderView, self).get_queryset()


class InboxedMessagesView(MessagesFolderView):
    """
    Show the list of messages that are in the inbox (i.e. not archived).
    """
    queryset_name = 'inbox'
    folder = 'inbox'
    folder_name = _(u'Inbox')


class SentMessagesView(MessagesFolderView):
    """
    Show the list of messages that the user sent himself.
    """
    queryset_name = 'sent'
    folder = 'sent'
    folder_name = _(u'Sent')


class ArchivedMessagesView(MessagesFolderView):
    """
    Show the list of messages that are in the archive.
    """
    queryset_name = 'archived'
    folder = 'archive'
    folder_name = _(u'Archive')


class TrashedMessagesView(MessagesFolderView):
    """
    Show the list of messages that are in the trash.
    """
    queryset_name = 'trashed'
    folder = 'trash'
    folder_name = _(u'Trash')


class ReadMessagesView(MessagesFolderView):
    """
    Show the list of messages that were read.
    """
    queryset_name = 'read'
    folder = 'read'
    folder_name = _(u'Read')


class UnreadMessagesView(MessagesFolderView):
    """
    Show the list of messages that are unread.
    """
    queryset_name = 'unread'
    folder = 'unread'
    folder_name = _(u'Unread')


# Message level views
# -------------------
class MessageView(LoginRequiredMixin, DetailView):
    """
    Display a message.
    """
    model = Message
    context_object_name = 'message'
    template_name = 'privmsg/message.html'

    def get_object(self):
        # Getting the message by pk is not enough, the message must belong to the user.
        object = get_object_or_404(self.model,
                                   pk=self.kwargs.get(self.pk_url_kwarg),
                                   recipient=self.request.user)
        object.mark_read()
        return object


class MessageToArchiveView(ConfirmActionMixin, MessageView):
    """
    Move message to the archive.
    """
    confirm_message = _(u'Do you want to archive this message?')
    success_message = _(u'The message was archived.')
    confirm_label = _(u'Archive')
    success_url = reverse_lazy('privmsg-archive')

    def confirm_action(self):
        self.object.archive()


class MessageToTrashView(ConfirmActionMixin, MessageView):
    """
    Move message to trash.
    """
    confirm_message = _(u'Do you want to move this message to trash?')
    success_message = _(u'The message was moved to trash.')
    confirm_label = _(u'Trash')
    success_url = reverse_lazy('privmsg-trash')

    def confirm_action(self):
        self.object.trash()


class MessageRestoreView(ConfirmActionMixin, MessageView):
    """
    Restore message from `trash` or `archive` to `inbox` or `sent`.
    """
    confirm_message = _(u'Do you want to restore this message?')
    success_message = _(u'The message has been restored.')
    confirm_label = _(u'Restore')

    def confirm_action(self):
        self.object.restore()

    def get_success_url(self):
        return self.object.get_absolute_url(action='folder')


class MessageDeleteView(ConfirmActionMixin, MessageView):
    """
    Delete a message.
    """
    confirm_message = _(u'Do you want to delete this message?')
    success_message = _(u'The message was deleted.')
    confirm_label = _(u'Delete')
    success_url = reverse_lazy('privmsg-inbox')

    def confirm_action(self):
        self.object.delete()


# Composing messages
# ------------------
class FormPreviewMixin(object):
    """
    Mixin to enable FormViews to display a preview.
    """

    def get_context_data(self, **kwargs):
        """
        Inject the preview into the context dict, if it was requested.
        """
        context = super(FormPreviewMixin, self).get_context_data(**kwargs)
        if 'preview' in self.request.POST:
            context['previews'] = self.render_previews()
        return context

    def render_previews(self):
        """
        Render the previews.
        """
        previews = {}
        preview_method = self.get_preview_method()

        for field in self.get_preview_fields():
            previews[field] = preview_method(self.request.POST.get(field, ''))
        return previews

    def get_preview_fields(self):
        """
        Return the list of form field names that should be rendered.
        """
        if hasattr(self, 'preview_fields'):
            return self.preview_fields
        else:
            raise ImproperlyConfigured(
                '{0} is missing the preview_fields attribute. Define {0}.preview_fields '
                'or overwrite {0}.get_preview_fields().'.format(self.__class__.__name__)
            )

    def get_preview_method(self):
        """
        Return the method (callable) that renders the preview.
        """
        if hasattr(self, 'preview_method'):
            return self.preview_method
        else:
            raise ImproperlyConfigured(
                '{0} is missing the preview_method attribute. Define {0}.preview_method '
                'or overwrite {0}.get_preview_method().'.format(self.__class__.__name__)
            )

    def post(self, request):
        """
        Process POST requests.

        We need to overwrite this method to make the preview work. If the word 'preview'
        is in the `request.POST` we want to show the form again, so we treat the form as
        invalid.
        """
        form = self.get_form()
        if form.is_valid() and 'preview' not in request.POST:
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


def preview_helper(self, text):
    """
    Render a preview
    """
    return MessageData.get_text_rendered(text)
    # Note: I really don't understand why it doesn't work if I just put
    # preview_method = getattr(MessageData, 'get_text_rendered')
    # on the `MessageComposeView` class. In that case the get_field_rendered
    # method will think it is a child of MessageComposeView and things break
    # horribly.


class MessageComposeView(LoginRequiredMixin, FormPreviewMixin, FormView):
    """
    View to compose private messages.
    """
    template_name = 'privmsg/compose.html'
    success_url = reverse_lazy('privmsg-sent')
    preview_fields = ['text']
    preview_method = preview_helper

    def get_form_class(self):
        """
        Get the form class based on user permission.
        """
        if self.request.user.can('send_group_pm'):
            return PrivilegedMessageComposeForm
        else:
            return MessageComposeForm

    def get_form_kwargs(self):
        """
        Make sure the form is called with the `user` argument
        """
        kwargs = super(MessageComposeView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """
        Commit the message to the database.
        """
        message = MessageData.objects.create(author=self.request.user,
                                             subject=form.cleaned_data['subject'],
                                             text=form.cleaned_data['text'],)
        message.send(recipients=form.cleaned_data['recipients'])
        messages.success(self.request, _(u'Your message has been sent.'))
        return super(MessageComposeView, self).form_valid(form)

    def get_initial(self):
        """
        Return the `initial` data for the form.
        """
        return {
            'recipients': self.kwargs.get('user', None)
        }


class MessageForwardView(MessageComposeView):
    """
    Forward a private message.
    """

    def get_initial(self):
        """
        Return the `inital` data for the form.
        """
        pm = get_object_or_404(Message,
                               pk=self.kwargs['pk'],
                               recipient=self.request.user)

        if not pm.subject.lower().startswith('fw:'):
            subject = u'Fw: {}'.format(pm.subject)
        else:
            subject = pm.subject

        return {
            'recipients': self.kwargs.get('user', None),
            'subject': subject,
            'text': quote_text(text=pm.text, author=pm.author,),
        }


class MessageReplyView(MessageComposeView):
    """
    Reply to a private message.
    """
    reply_to_all = False

    def get_initial(self):
        """
        Return the `inital` data for the form.
        """
        pm = get_object_or_404(Message.objects.include_related(),
                               pk=self.kwargs['pk'],
                               recipient=self.request.user)

        recipients = set([pm.author])
        if self.reply_to_all:
            recipients.update(pm.recipients)
        recipients.discard(self.request.user)
        recipients = ';'.join(r.username for r in recipients)

        if not pm.subject.lower().startswith('re:'):
            subject = u'Re: {}'.format(pm.subject)
        else:
            subject = pm.subject

        return {
            'recipients': recipients,
            'subject': subject,
            'text': quote_text(text=pm.text, author=pm.author),
        }


class MessageReplyReportedTopicView(MessageComposeView):
    """
    Reply to reported topics on the forum.
    """

    def get_initial(self):
        """
        Return the `inital` data for the form.
        """
        topic = get_object_or_404(Topic, slug=self.kwargs['slug'])

        if not have_privilege(self.request.user, topic.forum, CAN_MODERATE):
            return HttpResponseRedirect(reverse('privmsg-inbox'))

        recipient = User.objects.get(id=topic.reporter_id)
        return {
            'recipients': recipient,
            'subject': u'Re: {}'.format(topic.title),
            'text': quote_text(topic.reported, recipient),
        }


class MessageReplySuggestedArticleView(MessageComposeView):
    """
    Reply to suggested articles.
    """

    def get_initial(self):
        """
        Return the `inital` data for the form.
        """
        suggestion = get_object_or_404(Suggestion, pk=self.kwargs['suggestion_id'])

        recipient = suggestion.author
        subject = u'Re: {}'.format(suggestion.title)
        text = u'{}\n\n{}'.format(suggestion.intro, suggestion.text)
        text = quote_text(text, recipient)
        return {
            'recipients': recipient,
            'subject': subject,
            'text': text,
        }
