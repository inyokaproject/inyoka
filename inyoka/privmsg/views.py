# -*- coding: utf-8 -*-
"""
    inyoka.privmsg.views
    ~~~~~~~~~~~~~~~~~~~~

    Views for private messages between users.

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
# import locale

from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.http import HttpResponseRedirect
from django.views.generic.edit import FormView
from django.views.generic.list import ListView, MultipleObjectMixin
from django.views.generic import DetailView


from inyoka.forum.acl import CAN_MODERATE, have_privilege
from inyoka.forum.models import Topic
from inyoka.ikhaya.models import Suggestion
from inyoka.utils.django_19_auth_mixins import LoginRequiredMixin
from inyoka.utils.flash_confirmation import ConfirmActionMixin
from inyoka.utils.http import templated
from inyoka.utils.templating import render_template
from inyoka.portal.user import User
from inyoka.portal.utils import simple_check_login
from inyoka.privmsg.forms import MessageComposeForm, PrivilegedMessageComposeForm
from inyoka.privmsg.models import Message, MessageData
from inyoka.wiki.utils import quote_text


MESSAGES_PER_PAGE = 20


# "Folder" level views
# --------------------


# for reference, this would be the equivalent function based view:
@simple_check_login
@templated('privmsg/folder.html')
def inbox(request):
    """
    View the users private message inbox.
    """
    messages = request.user.message_set.inbox()
    # actually pagination is missing.
    return {
        'folder': 'inbox',
        'folder_name': _(u'Inbox'),
        'messages': messages,
    }


class BaseFolderMessagesView(LoginRequiredMixin, ListView, MultipleObjectMixin):
    """
    Base View to Show a list of private messages for a user.
    """
    template_name = 'privmsg/folder.html'
    context_object_name = 'messages'
    paginate_by = MESSAGES_PER_PAGE

    def get_context_data(self, **context):
        context = super(BaseFolderMessagesView, self).get_context_data()
        # we need two more keys to the context.
        context['folder'] = self.folder
        context['folder_name'] = self.folder_name
        return context

    def get_queryset(self):
        """
        Return the queryset.
        """
        if self.queryset_name is not None:
            # basically, take the `queryset_name` string and call it as a method
            # on the current users `message_set`
            q = getattr(self.request.user.message_set, self.queryset_name)
            return q()
        else:
            super(BaseFolderMessagesView, self).get_queryset()


class InboxedMessagesView(BaseFolderMessagesView):
    """
    Show the list of messages that are in the inbox (i.e. not archived).
    """
    queryset_name = 'inbox'
    folder = 'inbox'
    folder_name = _(u'Inbox')


class SentMessagesView(BaseFolderMessagesView):
    """
    Show the list of messages that the user sent himself.
    """
    queryset_name = 'sent'
    folder = 'sent'
    folder_name = _(u'Sent')


class ArchivedMessagesView(BaseFolderMessagesView):
    """
    Show the list of messages that are in the archive.
    """
    queryset_name = 'archived'
    folder = 'archive'
    folder_name = _(u'Archive')


class TrashedMessagesView(BaseFolderMessagesView):
    """
    Show the list of messages that are in the trash.
    """
    queryset_name = 'trashed'
    folder = 'trash'
    folder_name = _(u'Trash')


class ReadMessagesView(BaseFolderMessagesView):
    """
    Show the list of messages that were read.
    """
    queryset_name = 'read'
    folder = 'read'
    folder_name = _(u'Read')


class UnreadMessagesView(BaseFolderMessagesView):
    """
    Show the list of messages that are unread.
    """
    queryset_name = 'unread'
    folder = 'unread'
    folder_name = _(u'Unread')


# Message level views
# -------------------

# For reference, this is the function based view:
@simple_check_login
@templated('privmsg/message.html')
def message(request, pk=None):
    message = get_object_or_404(Message, pk=pk, recipient=request.user)
    message.mark_read()
    return {
        'message': message,
    }


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


# Moving stuff as function based view:
@simple_check_login
@templated('privmsg/message')
def message_archive(request, pk=None):
    message = get_object_or_404(Message, pk=pk, recipient=request.user)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            return HttpResponseRedirect(message.get_absolute_url())
        else:
            message.archive()
            return HttpResponseRedirect(reverse('privmsg-archive'))
    else:
        messages.info(request,
                      render_template('confirm_action_flash.html',
                                      {'message': _(u'Do you want to archive this message?'),
                                       'confirm_label': _(u'Archive'),
                                       'cancel_label': _(u'Cancel')},
                                      flash=True))
        return {
            'message': message,
        }


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
            context['preview'] = self.render_preview()
        return context

    def render_preview(self):
        """
        Render the preview.
        """
        p = getattr(self.preview_model, self.preview_method)
        return p(self.request.POST.get(self.preview_form_field, ''))
        # I don't know why this doesn't work if the getattr is defined in the class itself:
        # This would be so much easier and prettier.
        # return self.preview_callable(self.request.POST.get(self.preview_form_field, ''))

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


# for reference, the equivalent function based view:
# (no it's not pretty ;) but mostly because of the preview rendering)
# it only gets worse when replying or forwarding.
@simple_check_login
@templated('privmsg/compose.html')
def compose(request):
    preview = ''
    if request.method == 'POST':
        if request.user.can('send_group_pm'):
            form = PrivilegedMessageComposeForm(request.POST, user=request.user)
        else:
            form = MessageComposeForm(request.POST, user=request.user)
        if 'preview' in request.POST:
            preview = MessageData.get_text_rendered(request.POST.get('text', ''))
        elif form.is_valid():
            message = MessageData.objects.create(author=request.user,
                                                 subject=form.cleaned_data['subject'],
                                                 text=form.cleaned_data['text'],)
            message.send(form.cleaned_data['recipients'])
            messages.success(_(u'Your message has been sent.'))
            return HttpResponseRedirect(reverse('privmsg-sent'))
    elif request.user.can('send_group_pm'):
        form = PrivilegedMessageComposeForm(user=request.user)
    else:
        form = MessageComposeForm(user=request.user)

    return {
        'form': form,
        'preview': preview,
    }


class MessageComposeView(LoginRequiredMixin, FormPreviewMixin, FormView):
    """
    View to compose private messages.
    """
    template_name = 'privmsg/compose.html'
    success_url = reverse_lazy('privmsg-sent')
    preview_model = MessageData
    preview_method = 'get_text_rendered'
    preview_form_field = 'text'
    # preview_callable = getattr(MessageData, 'get_text_rendered')  # doesn't work?!

    def get_form_class(self):
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
        messages.success(_(u'Your message has been sent.'))
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
    def get_initial(self):
        """
        Return the `inital` data for the form.
        """
        pm = get_object_or_404(Message,
                               pk=self.kwargs['pk'],
                               recipient=self.request.user)

        recipients = set([pm.author])
        if self.kwargs.get('reply_to_all', False):
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
