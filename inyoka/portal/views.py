"""
    inyoka.portal.views
    ~~~~~~~~~~~~~~~~~~~

    All views for the portal including the user control panel, private messages,
    static pages and the login/register.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import csv
from datetime import date, datetime, timedelta
from functools import partial
from time import time

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.contrib.auth.views import (
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import IntegrityError
from django.forms.models import model_to_dict
from django.forms.utils import ErrorList
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.middleware.csrf import REASON_NO_CSRF_COOKIE, REASON_NO_REFERER
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dates import MONTHS, WEEKDAYS
from django.utils.html import escape
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.views.decorators.http import require_POST
from icalendar import Calendar as iCal
from icalendar import Event as iEvent
from PIL import Image

from inyoka.forum.models import Forum
from inyoka.ikhaya.models import Article, Category, Event
from inyoka.portal.filters import SubscriptionFilter
from inyoka.portal.forms import (
    NOTIFICATION_CHOICES,
    ConfigurationForm,
    CreateUserForm,
    DeactivateUserForm,
    EditFileForm,
    EditGroupForm,
    EditStaticPageForm,
    EditUserGroupsForm,
    EditUserProfileForm,
    EditUserStatusForm,
    ForumFeedSelectorForm,
    GroupForumPermissionForm,
    GroupGlobalPermissionForm,
    IkhayaFeedSelectorForm,
    LinkMapFormset,
    LoginForm,
    LostPasswordForm,
    PlanetFeedSelectorForm,
    PrivateMessageForm,
    PrivateMessageFormProtected,
    PrivateMessageIndexForm,
    RegisterForm,
    SubscriptionForm,
    TokenForm,
    UserCPProfileForm,
    UserCPSettingsForm,
    UserMailForm,
    WikiFeedSelectorForm,
)
from inyoka.portal.models import (
    PRIVMSG_FOLDERS,
    Linkmap,
    PrivateMessage,
    PrivateMessageEntry,
    StaticFile,
    StaticPage,
    Subscription,
)
from inyoka.portal.user import (
    User,
    deactivate_user,
    send_activation_mail,
)
from inyoka.portal.utils import (
    abort_access_denied,
    calendar_entries_for_month,
    get_ubuntu_versions,
    google_calendarize,
)
from inyoka.utils import generic
from inyoka.utils.http import (
    templated,
)
from inyoka.utils.mail import send_mail
from inyoka.utils.notification import send_notification
from inyoka.utils.pagination import Pagination
from inyoka.utils.sessions import get_sessions, get_user_record, make_permanent
from inyoka.utils.sortable import Sortable
from inyoka.utils.storage import storage
from inyoka.utils.templating import flash_message
from inyoka.utils.urls import href, is_safe_domain, url_for
from inyoka.utils.user import check_activation_key
from inyoka.wiki.models import Page as WikiPage
from inyoka.wiki.utils import quote_text

# TODO: move into some kind of config, but as a quick fix for now...
AUTOBAN_SPAMMER_WORDS = (
    ('million', 'us', 'dollar'),
    ('xxx', 'porn'),
    ('Sprachaustausch', 'gesundheitlich', 'immediately'),
)
# autoban gets active if all words of a tuple match


page_delete = generic.DeleteView.as_view(model=StaticPage,
    template_name='portal/page_delete.html',
    redirect_url=href('portal', 'pages'),
    permission_required='portal.delete_staticpage')


files = generic.ListView.as_view(model=StaticFile,
    paginate_by=0,
    default_column='identifier',
    template_name='portal/files.html',
    columns=['identifier', 'is_ikhaya_icon'],
    permission_required='portal.change_staticfile',
    base_link=href('portal', 'files'))


file_edit = generic.CreateUpdateView(model=StaticFile,
    form_class=EditFileForm,
    template_name='portal/file_edit.html',
    context_object_name='file', slug_field='identifier',
    permission_required='portal.change_staticfile')


file_delete = generic.DeleteView.as_view(model=StaticFile,
    template_name='portal/files_delete.html',
    redirect_url=href('portal', 'files'),
    slug_field='identifier',
    permission_required='portal.delete_staticfile')


@templated('portal/index.html')
def index(request):
    """
    Startpage that shows the latest ikhaya articles
    and some records of ubuntuusers.de
    """
    ikhaya_latest = Article.objects.get_latest_articles()

    storage_values = storage.get_many(('session_record',
        'session_record_time', 'countdown_active', 'countdown_target_page',
        'countdown_image_url', 'countdown_date'))

    record, record_time = get_user_record({
        'session_record': storage_values.get('session_record'),
        'session_record_time': storage_values.get('session_record_time')
    })

    countdown_active = storage_values.get('countdown_active', False) in (True, 'True')
    countdown_date = storage_values.get('countdown_date', None)
    countdown_image_url = storage_values.get('countdown_image_url', None)
    if countdown_active and countdown_date:
        release_date = None
        if isinstance(countdown_date, str):
            release_date = datetime.strptime(countdown_date, '%Y-%m-%d').date()
        else:
            release_date = None
        if release_date:
            countdown_remaining = (release_date - date.today()).days
            if countdown_remaining > 31:
                # We don't have images for > 31 days ahead
                countdown_active = False
            elif countdown_remaining > 0:
                # Format it with a leading zero
                countdown_remaining = '%02d' % countdown_remaining
            elif countdown_remaining <= 0:
                countdown_remaining = 'soon'
        else:
            countdown_active = False
    else:
        countdown_active = False
    if countdown_active:
        if countdown_remaining:
            countdown_image_url = countdown_image_url % {
                'remaining': countdown_remaining
            }

    return {
        'welcome_message_rendered': storage['welcome_message_rendered'],
        'ikhaya_latest': list(ikhaya_latest),
        'sessions': get_sessions(),
        'record': record,
        'record_time': record_time,
        'get_ubuntu_link': settings.INYOKA_GET_UBUNTU_LINK,
        'get_ubuntu_description': settings.INYOKA_GET_UBUNTU_DESCRIPTION,
        'events': cache.get_or_set('portal/calendar', partial(Event.objects.get_upcoming, 4), 300),
        'countdown_active': countdown_active,
        'countdown_target_page': storage_values.get('countdown_target_page', None),
        'countdown_image_url': countdown_image_url,
    }


@templated('portal/whoisonline.html')
def whoisonline(request):
    """Shows who is online and a link to the page the user views."""
    registered_users = cache.get_or_set('portal/registered_users',
                                        User.objects.count, 1000)
    record, record_time = get_user_record()

    return {
        'sessions': get_sessions(),
        'record': record,
        'record_time': record_time,
        'global_registered_users': registered_users
    }


@templated('portal/register.html')
def register(request):
    """Register a new user."""
    if settings.INYOKA_DISABLE_REGISTRATION:
        messages.error(request, _('User registration is currently disabled.'))
        return HttpResponseRedirect(href('portal'))

    redirect = (request.GET['next'] if is_safe_domain(request.GET.get('next'))
        else href('portal'))
    if request.user.is_authenticated:
        messages.error(request, _('You are already logged in.'))
        return HttpResponseRedirect(redirect)

    if request.method == 'POST' and 'renew_captcha' not in request.POST:
        form = RegisterForm(request.POST)
        form.captcha_solution = request.session.get('captcha_solution')
        if form.is_valid():
            data = form.cleaned_data

            try:
                user = User.objects.register_user(
                    username=data['username'],
                    email=data['email'],
                    password=data['password'])
            except IntegrityError:
                messages.info(request,
                              _('Please check whether you received an email with the activation key. If not, try '
                                'to register with another user name or email-address.'))
            else:
                messages.success(request,
                    _('The username “%(username)s” was successfully registered. '
                      'An email with the activation key was sent to '
                      '“%(email)s”.') % {
                          'username': escape(user.username),
                          'email': escape(user.email)})

            # clean up request.session
            request.session.pop('captcha_solution', None)
            return HttpResponseRedirect(redirect)
    else:
        form = RegisterForm()

    return {
        'form': form,
    }


def activate(request, action='', username='', activation_key=''):
    """Activate a user with the activation key send via email."""
    redirect = is_safe_domain(request.GET.get('next', ''))
    try:
        user = User.objects.get(username__iexact=username)
    except User.DoesNotExist:
        messages.error(request,
            _('The user “%(username)s” does not exist.') % {
                'username': escape(username)})
        return HttpResponseRedirect(href('portal'))
    if not redirect:
        redirect = href('portal', 'login', username=user.username)

    if request.user.is_authenticated:
        messages.error(request,
            _('You cannot enter an activation key when you are logged in.'))
        return HttpResponseRedirect(href('portal'))

    if action not in ('delete', 'activate'):
        raise Http404()

    if action == 'delete':
        if check_activation_key(user, activation_key):
            if not user.is_active:
                messages.success(request, _('Your account was anonymized.'))
            else:
                messages.error(request,
                    _('The account of “%(username)s” was already activated.') %
                    {'username': escape(username)})
        else:
            messages.error(request, _('Your activation key is invalid.'))
        return HttpResponseRedirect(href('portal'))
    else:
        if check_activation_key(user, activation_key) and user.is_inactive:
            user.status = User.STATUS_ACTIVE
            user.save()
            user.groups.add(Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME))
            messages.success(request,
                _('Your account was successfully activated. You can now '
                  'login.'))
            return HttpResponseRedirect(redirect)
        else:
            messages.error(request, _('Your activation key is invalid.'))
            return HttpResponseRedirect(href('portal'))


class InyokaPasswordResetView(SuccessMessageMixin, PasswordResetView):
    """
    If a users has lost his password, it is here possible to send an email
    with a one time link to his account-email-address. With this link he
    can set a new password at `InyokaPasswordResetConfirmView`.

    Customized to show an error, if the user is already logged in and
    to show a success message.
    """
    template_name = 'portal/lost_password.html'
    email_template_name = 'mails/new_user_password.txt'
    subject_template_name = 'mails/new_user_password_subject.txt'
    form_class = LostPasswordForm
    success_url = href('portal', 'login')
    success_message = _('An email with further instructions was sent to you.')

    def dispatch(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            messages.error(self.request, _('You are already logged in.'))
            return HttpResponseRedirect(href('portal'))

        return super().dispatch(*args, **kwargs)


class InyokaPasswordResetConfirmView(SuccessMessageMixin, PasswordResetConfirmView):
    """
    With the correct one time token this view allows to set a new password for an
    account.
    """
    success_url = href('portal', 'login')
    success_message = _('You successfully changed your password and are now '
                        'able to login.')
    template_name = 'portal/set_new_password.html'


@templated('portal/login.html')
def login(request):
    """Login dialog that supports permanent logins"""
    redirect = (request.GET['next'] if is_safe_domain(request.GET.get('next'))
                else href('portal'))

    if request.user.is_authenticated:
        messages.error(request, _('You are already logged in.'))
        return HttpResponseRedirect(redirect)

    if request.method == 'POST':
        form = LoginForm(request, request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = form.get_user()

            if data['permanent']:
                make_permanent(request)

            # username matches password and user is active
            messages.success(request, _('You have successfully logged in.'))
            auth.login(request, user)
            return HttpResponseRedirect(redirect)
    else:
        form = LoginForm()

    d = {
        'form': form,
    }

    return d


def logout(request):
    """Simple logout view that flashes if the process was done
    successful or not (e.g. if the user wasn't logged in)."""
    redirect = (request.GET['next'] if is_safe_domain(request.GET.get('next'))
                else href('portal'))

    if request.user.is_authenticated:
        if request.user.settings.get('mark_read_on_logout'):
            for forum in Forum.objects.get_categories().all():
                forum.mark_read(request.user)
        auth.logout(request)
        messages.success(request, _('You have successfully logged out.'))
    else:
        messages.error(request, _('You were not logged in.'))

    return HttpResponseRedirect(redirect)


@login_required
@templated('portal/profile.html')
def profile(request, username):
    """Show the user profile if the user is logged in."""

    user = User.objects.get(username__iexact=username)
    groups = user.groups.all()
    subscribed = Subscription.objects.user_subscribed(request.user, user)

    return {
        'user': user,
        'groups': groups,
        'User': User,
        'is_subscribed': subscribed,
    }


@login_required
@permission_required('portal.change_user', raise_exception=True)
@templated('portal/user_mail.html')
def user_mail(request, username):
    try:
        if '@' in username:
            user = User.objects.get(email__iexact=username)
        else:
            user = User.objects.get(username__iexact=username)
    except User.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = UserMailForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            message = render_to_string('mails/formmailer_template.txt', {
                'user': user,
                'text': text,
                'from': request.user.username,
            })
            send_mail(
                _('%(sitename)s - Message from %(username)s') % {
                    'sitename': settings.BASE_DOMAIN_NAME,
                    'username': request.user.username},
                message,
                settings.INYOKA_SYSTEM_USER_EMAIL,
                [user.email])
            messages.success(request,
                _('The email to “%(username)s” was sent successfully.')
                % {'username': escape(username)})
            return HttpResponseRedirect(request.GET.get('next') or href('portal', 'users'))
        else:
            generic.trigger_fix_errors_message(request)
    else:
        form = UserMailForm()

    return {
        'form': form,
        'user': user,
    }


@require_POST
@permission_required('portal.subscribe_user', raise_exception=True)
def subscribe_user(request, username):
    """Subscribe to a user to follow all of his activities."""
    user = User.objects.get(username__iexact=username)
    try:
        Subscription.objects.get_for_user(request.user, user)
    except Subscription.DoesNotExist:
        # there's no such subscription yet, create a new one
        Subscription(user=request.user, content_object=user).save()
        messages.info(request,
            _('You will now be notified about activities of “%(username)s”.')
            % {'username': user.username})
    return HttpResponseRedirect(url_for(user))


def unsubscribe_user(request, username):
    """Remove a user subscription."""
    user = User.objects.get(username__iexact=username)
    try:
        subscription = Subscription.objects.get_for_user(request.user, user)
    except Subscription.DoesNotExist:
        pass
    else:
        if request.method == 'POST':
            subscription.delete()
            messages.info(request,
                _('From now on you won’t be notified anymore about activities of '
                    '“%(username)s”.') % {'username': user.username})
        else:
            # ask for confirmation with form in case of GET (CSRF)
            flash_message(request, 'confirm_action_flash.html', {
                    'message': _('Do you want to unsubscribe from the user '
                                 '“%(username)s”?') % {'username': user.username},
                    'confirm_label': _('Unsubscribe'),
                    'cancel_label': _('Cancel'),
                    'action_url': request.build_absolute_uri(),
                })

    # redirect the user to the page he last watched
    if request.GET.get('next', False) and is_safe_domain(request.GET['next']):
        return HttpResponseRedirect(request.GET['next'])
    else:
        return HttpResponseRedirect(url_for(user))


@login_required
@templated('portal/usercp/index.html')
def usercp(request):
    """User control panel index page"""
    user = request.user
    return {
        'user': user,
    }


@login_required
@templated('portal/usercp/profile.html')
def usercp_profile(request):
    """User control panel view for changing the user's profile"""
    user = request.user
    if request.method == 'POST':
        form = UserCPProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save(request)
            messages.success(request, _('Your profile information were updated successfully.'))
            return HttpResponseRedirect(href('portal', 'usercp', 'profile'))
        else:
            generic.trigger_fix_errors_message(request)
    else:
        form = UserCPProfileForm(instance=user)

    return {
        'form': form,
        'user': request.user,
        'max_avatar_width': settings.INYOKA_AVATAR_MAXIMUM_WIDTH,
        'max_avatar_height': settings.INYOKA_AVATAR_MAXIMUM_HEIGHT,
        'max_avatar_size': settings.INYOKA_AVATAR_MAXIMUM_FILE_SIZE,
        'max_sig_length': settings.INYOKA_SIGNATURE_MAXIMUM_CHARACTERS,
    }


@login_required
@templated('portal/usercp/settings.html')
def usercp_settings(request):
    """User control panel view for changing various user settings"""
    if request.method == 'POST':
        form = UserCPSettingsForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            new_versions = data.pop('ubuntu_version')
            old_versions = [s.ubuntu_version for s in Subscription.objects
                          .filter(user=request.user).exclude(ubuntu_version__isnull=True)]
            for version in [v.number for v in get_ubuntu_versions()]:
                if version in new_versions and version not in old_versions:
                    Subscription(user=request.user, ubuntu_version=version).save()
                elif version not in new_versions and version in old_versions:
                    Subscription.objects.filter(user=request.user,
                                                ubuntu_version=version).delete()
            for key, value in data.items():
                request.user.settings[key] = data[key]
                if key == 'timezone':
                    timezone.activate(data[key])
                    request.session['django_timezone'] = data[key]
            request.user.save(update_fields=['settings'])
            messages.success(request, _('Your settings were successfully changed.'))
        else:
            generic.trigger_fix_errors_message(request)
    else:
        settings = request.user.settings
        ubuntu_version = [s.ubuntu_version for s in Subscription.objects.
                          filter(user=request.user, ubuntu_version__isnull=False)]
        values = {
            'notify': settings.get('notify', ['mail']),
            'notifications': settings.get('notifications', [c[0] for c in
                                                    NOTIFICATION_CHOICES]),
            'ubuntu_version': ubuntu_version,
            'timezone': timezone.get_current_timezone(),
            'hide_avatars': settings.get('hide_avatars', False),
            'hide_signatures': settings.get('hide_signatures', False),
            'hide_profile': settings.get('hide_profile', False),
            'autosubscribe': settings.get('autosubscribe', True),
            'show_preview': settings.get('show_preview', False),
            'show_thumbnails': settings.get('show_thumbnails', False),
            'highlight_search': settings.get('highlight_search', True),
            'mark_read_on_logout': settings.get('mark_read_on_logout', False),
            'reduce_motion': settings.get('reduce_motion', False)
        }
        form = UserCPSettingsForm(initial=values)
    return {
        'form': form,
        'user': request.user,
    }


class InyokaPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    """User control panel view for changing the password."""
    success_url = href('portal', 'usercp')
    success_message = _('Your password was changed successfully.')
    template_name = 'portal/usercp/change_password.html'


class UserCPSubscriptions(generic.FilterMixin, generic.OrderedListView):
    """This page shows all subscriptions for the current user and allows
    him to manage them.
    """
    template_name = 'portal/usercp/subscriptions.html'
    columns = ('notified',)
    order_by = ['-notified', '-id']
    context_object_name = 'subscriptions'
    base_link = href('portal', 'usercp', 'subscriptions')
    filtersets = [SubscriptionFilter]
    required_login = True
    permission_required = ()

    def get_queryset(self):
        qs = self.request.user.subscription_set.all()
        qs = qs.filter(ubuntu_version__isnull=True)
        for f in self.filtersets:
            instance = f(self.request.GET or None, queryset=qs)
            qs = instance.qs
        return qs

    def post(self, request, *args, **kwargs):
        form = SubscriptionForm(request.POST)
        subscriptions = self.get_queryset()

        if 'delete' in request.POST:
            form.fields['select'].choices = [(s.id, '') for s in subscriptions]
            if form.is_valid():
                d = form.cleaned_data
                Subscription.objects.delete_list(request.user.id, d['select'])
                msg = ngettext('A subscription was deleted.',
                                '%(n)d subscriptions were deleted.',
                                len(d['select']))
                messages.success(request, msg % {'n': len(d['select'])})

        if 'mark_read' in request.POST:
            form.fields['select'].choices = [(s.id, '') for s in subscriptions]
            if form.is_valid():
                d = form.cleaned_data
                Subscription.objects.mark_read_list(request.user.id, d['select'])
                msg = ngettext('A subscription was marked as read.',
                                '%(n)d subscriptions were marked as read.',
                                len(d['select']))
                messages.success(request, msg % {'n': len(d['select'])})

        return HttpResponseRedirect(href('portal', 'usercp', 'subscriptions'))


usercp_subscriptions = UserCPSubscriptions.as_view()


@login_required
@templated('portal/usercp/deactivate.html')
def usercp_deactivate(request):
    """
    This page allows the user to deactivate his account.
    """
    if request.method == 'POST':
        form = DeactivateUserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            check = data['password_confirmation']
            if not request.user.check_password(check):
                form.errors['password_confirmation'] = ErrorList(
                    [_('The entered password is wrong.')])

        if form.is_valid():
            deactivate_user(request.user)
            auth.logout(request)
            messages.success(request, _('Your account was deactivated.'))
            return HttpResponseRedirect(href('portal'))
        else:
            generic.trigger_fix_errors_message(request)
    else:
        form = DeactivateUserForm()
    return {
        'form': form,
        'user': request.user,
    }


@login_required
@permission_required('portal.change_user', raise_exception=True)
@templated('portal/user_overview.html')
def user_edit(request, username):
    try:
        user = User.objects.get_by_username_or_email(username)
    except User.DoesNotExist:
        raise Http404

    return {
        'user': user
    }


@login_required
@permission_required('portal.change_user', raise_exception=True)
@templated('portal/user_edit_profile.html')
def user_edit_profile(request, username):
    try:
        user = User.objects.get_by_username_or_email(username)
    except User.DoesNotExist:
        raise Http404

    form = EditUserProfileForm(instance=user, admin_mode=True)
    if request.method == 'POST':
        form = EditUserProfileForm(request.POST, request.FILES,
                                   instance=user, admin_mode=True)
        if form.is_valid():
            user = form.save(request)
            messages.success(request,
                _('The profile of “%(username)s” was changed successfully')
                % {'username': escape(user.username)})
            # redirect to the new username if given
            if user.username != username:
                return HttpResponseRedirect(href('portal', 'user', user.username, 'edit', 'profile'))
        else:
            generic.trigger_fix_errors_message(request)
    return {
        'user': user,
        'form': form,
        'avatar_height': settings.INYOKA_AVATAR_MAXIMUM_HEIGHT,
        'avatar_width': settings.INYOKA_AVATAR_MAXIMUM_WIDTH
    }


@login_required
@permission_required('portal.change_user', raise_exception=True)
@templated('portal/user_edit_settings.html')
def user_edit_settings(request, username):
    try:
        user = User.objects.get_by_username_or_email(username)
    except User.DoesNotExist:
        raise Http404

    ubuntu_version = [s.ubuntu_version for s in Subscription.objects.
                      filter(user=user, ubuntu_version__isnull=False)]
    initial = {
        'notify': user.settings.get('notify', ['mail']),
        'notifications': user.settings.get('notifications',
            [c[0] for c in NOTIFICATION_CHOICES]),
        'ubuntu_version': ubuntu_version,
        'timezone': timezone.get_current_timezone(),
        'hide_avatars': user.settings.get('hide_avatars', False),
        'hide_signatures': user.settings.get('hide_signatures', False),
        'hide_profile': user.settings.get('hide_profile', False),
        'autosubscribe': user.settings.get('autosubscribe', True),
        'show_preview': user.settings.get('show_preview', False),
        'show_thumbnails': user.settings.get('show_thumbnails', False),
        'highlight_search': user.settings.get('highlight_search', True),
        'mark_read_on_logout': user.settings.get('mark_read_on_logout', False)
    }
    form = UserCPSettingsForm(initial=initial)
    if request.method == 'POST':
        form = UserCPSettingsForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            new_versions = data.pop('ubuntu_version')
            old_versions = [s.ubuntu_version for s in Subscription.objects
                          .filter(user=user).exclude(ubuntu_version__isnull=True)]
            for version in [v.number for v in get_ubuntu_versions()]:
                if version in new_versions and version not in old_versions:
                    Subscription(user=user, ubuntu_version=version).save()
                elif version not in new_versions and version in old_versions:
                    Subscription.objects.filter(user=user,
                                                ubuntu_version=version).delete()
            for key, value in data.items():
                user.settings[key] = data[key]
            user.save()
            messages.success(request,
                _('The setting of “%(username)s” were successfully changed.')
                % {'username': escape(user.username)})
    return {
        'user': user,
        'form': form
    }


@login_required
@permission_required('portal.change_user', raise_exception=True)
@templated('portal/user_edit_status.html')
def user_edit_status(request, username):
    try:
        user = User.objects.get_by_username_or_email(username)
    except User.DoesNotExist:
        raise Http404

    form = EditUserStatusForm(instance=user)
    if request.method == 'POST':
        form = EditUserStatusForm(request.POST, instance=user)
        if form.is_valid():
            user.save()
            if user.status != User.STATUS_ACTIVE:
                user.groups.clear()
            messages.success(request,
                _('The state of “%(username)s” was successfully changed.')
                % {'username': escape(user.username)})
    if not user.is_inactive:
        activation_link = None
    else:
        activation_link = user.get_absolute_url('activate')
    return {
        'user': user,
        'form': form,
        'activation_link': activation_link
    }


@login_required
@permission_required('portal.change_user', raise_exception=True)
@templated('portal/user_edit_groups.html')
def user_edit_groups(request, username):
    try:
        user = User.objects.get_by_username_or_email(username)
    except User.DoesNotExist:
        raise Http404

    initial = model_to_dict(user)
    form = EditUserGroupsForm(initial=initial)
    if request.method == 'POST':
        form = EditUserGroupsForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request,
                _('The groups of “%(username)s” were successfully changed.')
                % {'username': escape(user.username)})
        else:
            generic.trigger_fix_errors_message(request)
    return {
        'user': user,
        'form': form,
    }


@login_required
@permission_required('portal.add_user', raise_exception=True)
@templated('portal/user_new.html')
def user_new(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            User.objects.register_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                send_mail=data['authenticate'])
            messages.success(request,
                _('The user “%(username)s” was successfully created. '
                  'You can now edit more details.')
                % {'username': escape(data['username'])})
            return HttpResponseRedirect(href('portal', 'user',
                        escape(data['username']), 'edit'))
        else:
            generic.trigger_fix_errors_message(request)
    else:
        form = CreateUserForm()
    return {
        'form': form
    }


@login_required
@permission_required('portal.change_user', raise_exception=True)
def admin_resend_activation_mail(request):
    user = User.objects.get(username__iexact=request.GET.get('user'))
    if not user.is_inactive:
        messages.error(request,
            _('The account of “%(username)s” was already activated.')
            % {'username': user.username})
    else:
        send_activation_mail(user)
        messages.success(request,
            _('The email with the activation key was resent.'))
    return HttpResponseRedirect(request.GET.get('next') or href('portal', 'users'))


@login_required
@templated('portal/privmsg/index.html')
def privmsg(request, folder=None, entry_id=None, page=1, one_page=False):
    page = int(page)
    if folder is None:
        if entry_id is None:
            return HttpResponseRedirect(href('portal', 'privmsg', 'inbox'))
        else:
            try:
                entry = PrivateMessageEntry.objects.get(user=request.user,
                                                        id=entry_id)
                return HttpResponseRedirect(href('portal', 'privmsg',
                                                 PRIVMSG_FOLDERS[entry.folder][1],
                                                 entry.id))
            except KeyError:
                raise Http404

    if folder not in list(PRIVMSG_FOLDERS.keys()):
        raise Http404

    entries = PrivateMessageEntry.objects.filter(
        user=request.user,
        folder=PRIVMSG_FOLDERS[folder][0]
    ).select_related('message__author').order_by('-id')

    if request.method == 'POST':
        # POST is only send by the "delete marked messages" button
        form = PrivateMessageIndexForm(request.POST)
        form.fields['delete'].choices = [(pm.id, '') for pm in entries]
        if form.is_valid():
            d = form.cleaned_data
            PrivateMessageEntry.delete_list(request.user.id, d['delete'])
            msg = ngettext('A message was deleted.',
                            '%(n)d messages were deleted.',
                            len(d['delete']))
            messages.success(request, msg % {'n': len(d['delete'])})
            entries = [s for s in entries if str(s.id) not in d['delete']]
            cache.delete(f'portal/pm_count/{request.user.id}')
            return HttpResponseRedirect(href('portal', 'privmsg',
                                             PRIVMSG_FOLDERS[folder][1]))

    if entry_id is not None:
        entry = PrivateMessageEntry.objects.get(user=request.user,
            folder=PRIVMSG_FOLDERS[folder][0], id=entry_id)
        message = entry.message
        if not entry.read:
            entry.read = True
            entry.save()
            cache.delete(f'portal/pm_count/{request.user.id}')
        action = request.GET.get('action')
        if action:
            if request.method == 'POST':
                if 'cancel' in request.POST:
                    return HttpResponseRedirect(href('portal', 'privmsg',
                        folder, entry.id))
                if action == 'archive':
                    if entry.archive():
                        messages.success(request, _('The messages was moved into you archive.'))
                        return HttpResponseRedirect(href('portal', 'privmsg'))
                elif action == 'restore':
                    if entry.restore():
                        messages.success(request, _('The message was restored.'))
                        return HttpResponseRedirect(href('portal', 'privmsg'))
                elif action == 'delete':
                    msg = _('The message was deleted.') if \
                        entry.folder == PRIVMSG_FOLDERS['trash'][0] else \
                        _('The message was moved in the trash.')
                    if entry.delete():
                        messages.success(request, msg)
                        return HttpResponseRedirect(href('portal', 'privmsg'))
            else:
                if action == 'archive':
                    msg = _('Do you want to archive the message?')
                    # confirm_label = pgettext('the verb "to archive", not the '
                    #                         'noun.', 'Archive')
                    confirm_label = _('Archive it')
                elif action == 'restore':
                    msg = _('Do you want to restore the message?')
                    confirm_label = _('Restore')
                elif action == 'delete':
                    msg = _('Do you really want to delete the message?')
                    confirm_label = _('Delete')
                flash_message(request, 'confirm_action_flash.html', {
                    'message': msg,
                    'confirm_label': confirm_label,
                    'cancel_label': _('Cancel'),
                })
    else:
        message = None
    link = href('portal', 'privmsg', folder, 'page')

    pagination = Pagination(request, query=entries, page=page, per_page=10, link=link, one_page=one_page)

    return {
        'entries': pagination.get_queryset(),
        'pagination': pagination,
        'folder': {
            'name': PRIVMSG_FOLDERS[folder][2],
            'id': PRIVMSG_FOLDERS[folder][1]
        },
        'message': message,
        'one_page': one_page,
    }


@login_required
@templated('portal/privmsg/new.html')
def privmsg_new(request, username=None):
    # if the user has no posts in the forum and registered less than a week ago
    # he can only send one pm every 5 minutes
    form_class = PrivateMessageForm
    if (not request.user.post_count and request.user.date_joined > (datetime.utcnow() - timedelta(days=7))):
        form_class = PrivateMessageFormProtected
    preview = None
    form = form_class()
    if request.method == 'POST':
        form = form_class(request.POST)
        if 'preview' in request.POST:
            preview = PrivateMessage.get_text_rendered(request.POST.get('text', ''))
        elif form.is_valid():
            d = form.cleaned_data

            for group in AUTOBAN_SPAMMER_WORDS:
                t = d['text']
                if all([x in t for x in group]):
                    if '>' in t:
                        continue  # User quoted, most likely a forward and no spam
                    request.user.status = User.STATUS_BANNED
                    request.user.banned_until = None
                    request.user.save(update_fields=['status', 'banned_until'])
                    messages.info(request,
                        _('You were automatically banned because we suspect '
                          'you are sending spam. If this ban is not '
                          'justified, contact us at %(email)s')
                        % {'email': settings.INYOKA_CONTACT_EMAIL})
                    auth.logout(request)
                    return HttpResponseRedirect(href('portal'))

            recipient_names = {r.strip() for r in
                                  d['recipient'].split(';') if r}
            group_recipient_names = {r.strip() for r in
                                  d['group_recipient'].split(';') if r}

            recipients = set()

            if d.get('group_recipient', None) and not request.user.has_perm('portal.send_group_privatemessage'):
                messages.error(request, _('You cannot send messages to groups.'))
                return HttpResponseRedirect(href('portal', 'privmsg'))

            for group in group_recipient_names:
                try:
                    users = Group.objects.get(name__iexact=group).user_set.\
                        all().exclude(pk=request.user.id)
                    recipients.update(users)
                except Group.DoesNotExist:
                    messages.error(request,
                        _('The group “%(group)s” does not exist.')
                        % {'group': escape(group)})
                    return HttpResponseRedirect(href('portal', 'privmsg'))

            try:
                for recipient in recipient_names:
                    user = User.objects.get(username__iexact=recipient)
                    if user.id == request.user.id:
                        recipients = None
                        messages.error(request, _('You cannot send messages to yourself.'))
                        break
                    elif user in (User.objects.get_system_user(),
                                  User.objects.get_anonymous_user()):
                        recipients = None
                        messages.error(request, _('You cannot send messages to system users.'))
                        break
                    elif not user.is_active:
                        recipients = None
                        messages.error(request, (_('You cannot send messages to this user.')))
                        break
                    else:
                        recipients.add(user)
            except User.DoesNotExist:
                recipients = None
                messages.error(request,
                    _('The user “%(username)s” does not exist.')
                    % {'username': escape(recipient)})

            if recipients:
                msg = PrivateMessage()
                msg.author = request.user
                msg.subject = d['subject']
                msg.text = d['text']
                msg.pub_date = datetime.utcnow()
                msg.send(list(recipients))
                # send notification
                for recipient in recipients:
                    entry = PrivateMessageEntry.objects.get(message=msg,
                                                            user=recipient)
                    if 'pm_new' in recipient.settings.get('notifications',
                                                          ('pm_new',)):
                        send_notification(recipient, 'new_pm',
                            _('New private message from %(username)s: %(subject)s')
                            % {'username': request.user.username, 'subject': d['subject']},
                            {'user': recipient,
                             'sender': request.user,
                             'subject': d['subject'],
                             'entry': entry})

                messages.success(request, _('The message was sent successfully.'))

            return HttpResponseRedirect(href('portal', 'privmsg'))
    else:
        data = {}
        reply_to = request.GET.get('reply_to', '')
        reply_to_all = request.GET.get('reply_to_all', '')
        forward = request.GET.get('forward', '')
        try:
            int(reply_to or reply_to_all or forward)
        except ValueError:
            if ':' in (reply_to or reply_to_all or forward):
                return HttpResponseRedirect(href('portal', 'privmsg'))
        else:
            try:
                entry = PrivateMessageEntry.objects.get(user=request.user,
                    message=int(reply_to or reply_to_all or forward))
                msg = entry.message
                data['subject'] = msg.subject
                if reply_to or reply_to_all:
                    data['recipient'] = msg.author.username
                    if not data['subject'].lower().startswith('re: '):
                        data['subject'] = 'Re: %s' % data['subject']
                if reply_to_all:
                    data['recipient'] += ';' + ';'.join(x.username for x in msg.recipients if x != request.user)
                if forward and not data['subject'].lower().startswith('fw: '):
                    data['subject'] = 'Fw: %s' % data['subject']
                data['text'] = quote_text(msg.text, msg.author) + '\n'
                form = PrivateMessageForm(initial=data)
            except (PrivateMessageEntry.DoesNotExist):
                pass
        if username:
            form = PrivateMessageForm(initial={'recipient': username})
    return {
        'form': form,
        'preview': preview
    }


class MemberlistView(generic.ListView):
    """Shows a list of all registered users."""
    template_name = 'portal/memberlist.html'
    columns = ('id', 'username', 'location', 'date_joined')
    context_object_name = 'users'
    model = User
    base_link = href('portal', 'users')
    permission_required = ()

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm('portal.change_user'):
            messages.error(request, _('You need to be logged in before you can continue.'))
            return abort_access_denied(request)
        name = request.POST.get('user')
        try:
            user = User.objects.get_by_username_or_email(name)
        except User.DoesNotExist:
            messages.error(request,
                _('The user “%(username)s” does not exist.')
                % {'username': escape(name)})
            return HttpResponseRedirect(request.build_absolute_uri())
        else:
            return HttpResponseRedirect(user.get_absolute_url('admin'))


memberlist = MemberlistView.as_view()


@login_required
@templated('portal/grouplist.html')
def grouplist(request, page=1):
    """
    Shows the group list.

    `page` represents the current page in the pagination.
    """
    groups = Group.objects.all()
    user_groups = request.user.groups.all()
    table = Sortable(groups, request.GET, 'name',
                     columns=['id', 'name'])
    pagination = Pagination(request, table.get_queryset(), page, 50,
                            link=href('portal', 'groups'))
    return {
        'groups': pagination.get_queryset(),
        'group_count': len(groups),
        'user_groups': user_groups,
        'pagination': pagination,
        'table': table
    }


@login_required
@templated('portal/group.html')
def group(request, name, page=1):
    """Shows the informations about the group named `name`."""
    if name == settings.INYOKA_REGISTERED_GROUP_NAME and not request.user.has_perm('portal.change_user'):
        raise Http404
    group = Group.objects.get(name__iexact=name)
    users = group.user_set.all()

    table = Sortable(users, request.GET, 'id',
        columns=['id', 'username', 'location', 'date_joined'])
    pagination = Pagination(request, table.get_queryset(), page, 15,
                            link=href('portal', 'group', name))
    return {
        'group': group,
        'users': pagination.get_queryset(),
        'user_count': group.user_set.count(),
        'pagination': pagination,
        'table': table,
    }


@login_required
@permission_required('auth.add_group', raise_exception=True)
@templated('portal/group_edit.html')
def group_new(request):
    form = EditGroupForm()
    if request.method == 'POST':
        form = EditGroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            messages.success(request,
                _('The group “%s” was created successfully.') % group.name)
            return HttpResponseRedirect(href('portal', 'group', group.name, 'edit'))
    return {
        'form': form,
    }


@login_required
@permission_required('auth.change_group', raise_exception=True)
@templated('portal/group_edit.html')
def group_edit(request, name):
    try:
        group = Group.objects.get(name=name)
    except Group.DoesNotExist:
        messages.error(request,
            _('The group “%(group)s” does not exist.')
            % {'group': escape(name)})
        return HttpResponseRedirect(href('portal', 'groups'))

    if request.method == 'POST':
        form = EditGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request,
                _('The group “%s” was changed successfully.') % group.name)
            return HttpResponseRedirect(href('portal', 'group', group.name, 'edit'))
    else:
        form = EditGroupForm(instance=group)

    return {
        'form': form,
        'group': group,
    }


@login_required
@permission_required('auth.change_group', raise_exception=True)
@templated('portal/group_edit_global_permissions.html')
def group_edit_global_permissions(request, name):
    group = get_object_or_404(Group, name=name)

    if request.method == 'POST':
        form = GroupGlobalPermissionForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request,
                _('The group “%s” was changed successfully.') % group.name)
            return HttpResponseRedirect(href('portal', 'group', group.name, 'edit', 'global_permissions'))
    else:
        form = GroupGlobalPermissionForm(instance=group)

    return {
        'group': group,
        'form': form,
    }

@login_required
@permission_required('auth.change_group', raise_exception=True)
@templated('portal/group_edit_forum_permissions.html')
def group_edit_forum_permissions(request, name):
    group = get_object_or_404(Group, name=name)

    if request.method == 'POST':
        form = GroupForumPermissionForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request,
                _('The group “%s” was changed successfully.') % group.name)
            return HttpResponseRedirect(href('portal', 'group', group.name, 'edit', 'forum_permissions'))
    else:
        form = GroupForumPermissionForm(instance=group)

    return {
        'group': group,
        'form': form,
    }


def usermap(request):
    messages.info(request, _('The user map was temporarily disabled.'))
    return HttpResponseRedirect(href('portal'))


app_feed_forms = {
    'forum': ForumFeedSelectorForm,
    'ikhaya': IkhayaFeedSelectorForm,
    'planet': PlanetFeedSelectorForm,
    'wiki': WikiFeedSelectorForm
}


@templated('portal/feedselector.html')
def feedselector(request, app=None):
    forms = {}
    for fapp in ('forum', 'ikhaya', 'planet', 'wiki'):
        if app in (fapp, None):
            args = {'data': request.POST, 'auto_id': 'id_%s_%%s' % fapp}
            forms[fapp] = (request.POST and app_feed_forms[fapp](**args)
                           or app_feed_forms[fapp](auto_id='id_%s_%%s' % fapp))
        else:
            forms[fapp] = None
    if forms['forum'] is not None:
        anonymous_user = User.objects.get_anonymous_user()
        forums = [forum for forum in Forum.objects.get_cached() if anonymous_user.has_perm('forum.view_forum', forum)]
        forms['forum'].fields['forum'].choices = [('', _('Please choose'))] + \
            [(f.slug, f.name) for f in forums]
    if forms['ikhaya'] is not None:
        forms['ikhaya'].fields['category'].choices = [('*', _('All'))] + \
            [(c.slug, c.name) for c in Category.objects.all()]
    if forms['wiki'] is not None:
        wiki_pages = cache.get('feedselector/wiki/pages')
        if not wiki_pages:
            wiki_pages = WikiPage.objects.get_page_list()
            cache.set('feedselector/wiki/pages', wiki_pages)
        forms['wiki'].fields['page'].choices = [('*', _('All'))] + \
            [(p, p) for p in wiki_pages]

    if request.method == 'POST':
        form = forms[app]
        if form.is_valid():
            data = form.cleaned_data
            if app == 'forum':
                if data['component'] == '*':
                    return HttpResponseRedirect(href('forum', 'feeds',
                           data['mode'], data['count']))
                if data['component'] == 'forum':
                    return HttpResponseRedirect(href('forum', 'feeds', 'forum',
                           data['forum'], data['mode'], data['count']))

            elif app == 'ikhaya':
                if data['category'] == '*':
                    return HttpResponseRedirect(href('ikhaya', 'feeds',
                           data['mode'], data['count']))
                else:
                    return HttpResponseRedirect(href('ikhaya', 'feeds',
                           data['category'], data['mode'], data['count']))

            elif app == 'planet':
                return HttpResponseRedirect(href('planet', 'feeds',
                       data['mode'], data['count']))

            elif app == 'wiki':
                if data['page'] == '*' or not data['page']:
                    return HttpResponseRedirect(href('wiki', '_feed',
                           data['count']))
                else:
                    return HttpResponseRedirect(href('wiki', data['page'],
                           'a', 'feed', data['count']))

    return {
        'app': app,
        'forum_form': forms['forum'],
        'ikhaya_form': forms['ikhaya'],
        'planet_form': forms['planet'],
        'wiki_form': forms['wiki'],
    }


@templated('portal/about_inyoka.html')
def about_inyoka(request):
    """Render a inyoka information page."""
    return {}


@templated('portal/calendar_month.html')
def calendar_month(request, year, month):
    year = int(year)
    month = int(month)
    if year < 1900 or month < 1 or month > 12:
        raise Http404
    days = calendar_entries_for_month(year, month)
    days = [(date(year, month, day), events) for day, events in list(days.items())]

    return {
        'days': days,
        'year': year,
        'month': month,
        'today': datetime.utcnow().date(),
        'MONTHS': MONTHS,
        'WEEKDAYS': WEEKDAYS,
    }


@templated('portal/calendar_overview.html')
def calendar_overview(request):
    events = Event.objects.get_upcoming(10)

    return {
        'events': events,
        'year': datetime.utcnow().year,
        'month': datetime.utcnow().month,
        'MONTHS': MONTHS,
        'WEEKDAYS': WEEKDAYS,
    }


@templated('portal/calendar_detail.html')
def calendar_detail(request, slug):
    try:
        event = Event.objects.get(slug=slug)
        if not event.visible:
            if request.user.has_perm('portal.change_event'):
                messages.info(request, _('This event is not visible for regular users.'))
            else:
                raise Http404()
    except Event.DoesNotExist:
        raise Http404()
    return {
        'google_link': google_calendarize(event),
        'ical_link': href('portal', 'calendar', slug, 'ics'),
        'event': event,
        'MONTHS': MONTHS,
        'WEEKDAYS': WEEKDAYS,
    }


def calendar_ical(request, slug):

    try:
        event = Event.objects.get(slug=slug)
        if not event.visible and not request.user.has_perm('portal.change_event'):
            raise Http404()

    except Event.DoesNotExist:
        raise Http404()

    cal = iCal()
    current_time = datetime.now().time()

    start = datetime.combine(event.date, event.time or current_time)

    if event.enddate:
        end = datetime.combine(event.enddate, event.endtime or current_time)
    else:
        end = start

    ievent = iEvent()
    ievent.add('summary', event.name)
    ievent.add('uid', slug)
    ievent.add('dtstamp', datetime.utcnow())
    ievent.add('dtstart', start)
    ievent.add('dtend', end)
    if event.description:
        ievent.add('description', event.description)

    location = '%s%s%s' % ((event.location and event.location + ', ' or ''), (event.location_town and event.location_town + ', ' or ''), (event.simple_coordinates != 'None;None' and event.simple_coordinates + ', ' or ''))

    ievent.add('location', location.rstrip(', '))

    cal.add_component(ievent)

    response = HttpResponse(content_type='text/calendar')
    response['Content-Disposition'] = 'attachment; filename="calendar.ics"'
    response.write(cal.to_ical())

    return response


@templated('portal/confirm.html')
def confirm(request, action):
    if action == 'reactivate_user' and request.user.is_authenticated:
        messages.error(request, _('You cannot reactivate an account while '
                                  'you are logged in.'))
        return abort_access_denied(request)
    elif action in ['set_new_email', 'reset_email'] and request.user.is_anonymous:
        messages.error(request, _('You need to be logged in before you can continue.'))
        return abort_access_denied(request)

    if request.method == 'POST':
        form = TokenForm(request.POST, action=action)

        if form.is_valid():
            messages.success(request, form.cleaned_data['token'])
            if request.user.is_authenticated:
                return HttpResponseRedirect(href('portal', 'usercp'))
            else:
                return HttpResponseRedirect(href('portal'))
    else:
        form = TokenForm(initial={'token': request.GET.get('token', '')})

    return {'action': action,
            'form': form}


@login_required
@permission_required('portal.change_storage', raise_exception=True)
@templated('portal/configuration.html')
def config(request):
    keys = ['welcome_message', 'license_note', 'blocked_hosts',
            'wiki_edit_note', 'wiki_newpage_template', 'wiki_newpage_root',
            'wiki_newpage_infopage', 'wiki_edit_note', 'distri_versions',
            'countdown_active', 'countdown_target_page', 'countdown_image_url',
            'ikhaya_description', 'planet_description']

    team_icon = storage['team_icon']

    if request.method == 'POST':
        form = ConfigurationForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            for k in keys:
                storage[k] = data[k]

            if data['global_message'] != storage['global_message']:
                storage['global_message'] = data['global_message']
                storage['global_message_time'] = time()

            if data['team_icon']:
                if storage['team_icon']:
                    default_storage.delete(storage['team_icon'])
                with Image.open(data['team_icon']) as icon:
                    fn = 'portal/global_team_icon.%s' % icon.format.lower()
                default_storage.save(fn, data['team_icon'], max_length=100)
                storage['team_icon'] = team_icon = fn

            if not data['countdown_date']:
                storage['countdown_date'] = ''
            else:
                storage['countdown_date'] = str(data['countdown_date'])

            messages.success(request, _('Your settings have been changed successfully.'))
        else:
            generic.trigger_fix_errors_message(request)
    else:
        storage['distri_versions'] = storage['distri_versions'] or '[]'
        form = ConfigurationForm(initial=storage.get_many(keys +
                                                ['global_message', 'countdown_date']))

    return {
        'form': form,
        'team_icon_url': team_icon and href('media', team_icon) or None,
        'versions': get_ubuntu_versions(),
    }


@templated('portal/static_page.html')
def static_page(request, page):
    """Renders static pages"""
    p = StaticPage.objects.get(key=page)

    return {
        'title': p.title,
        'content': p.content_rendered,
        'key': p.key,
        'page': p,
    }


@login_required
@permission_required('portal.change_staticpage', raise_exception=True)
@templated('portal/pages.html')
def pages(request):
    sortable = Sortable(StaticPage.objects.all(), request.GET, '-key',
        columns=['key', 'title'])
    return {
        'table': sortable,
        'pages': sortable.get_queryset(),
    }


@login_required
@permission_required('portal.change_staticpage', raise_exception=True)
@templated('portal/page_edit.html')
def page_edit(request, page=None):
    preview = None
    new = not bool(page)

    if page:
        page = StaticPage.objects.get(key=page)

    if request.method == 'POST':
        form = EditStaticPageForm(request.POST, instance=page)
        if form.is_valid():
            if 'preview' in request.POST:
                preview = StaticPage.get_content_rendered(
                    form.cleaned_data['content'])
            if 'send' in request.POST:
                page = form.save()
                if new:
                    msg = _('The page “%(page)s” was created successfully.')
                else:
                    msg = _('The page “%(page)s” was changed successfully.')
                messages.success(request, msg % {'page': page.title})
                return HttpResponseRedirect(href('portal', page.key))
    else:
        form = EditStaticPageForm(instance=page)

    return {
        'form': form,
        'page': page,
        'preview': preview
    }


def ikhaya_redirect(request, id):
    article = get_object_or_404(Article, pk=int(id))
    return HttpResponseRedirect(url_for(article))


def csrf_failure(request, reason=None):
    context = {
        'no_cookie': reason == REASON_NO_CSRF_COOKIE,
        'no_referer': reason == REASON_NO_REFERER,
    }

    return render(request, 'errors/403_csrf.html', context, status=403)


@login_required
@permission_required('portal.change_linkmap', raise_exception=True)
@templated('portal/linkmap.html')
def linkmap_edit(request):
    formset = partial(LinkMapFormset, queryset=Linkmap.objects.order_by('token'))

    if request.method == 'POST':
        formset = formset(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            Linkmap.objects.flush_cache()
            return HttpResponseRedirect(href('portal', 'linkmap'))
    else:
        formset = formset()
    return {
        'formset': formset
    }


def linkmap_export(request):
    """Exports all current links of the Linkmap. Useful f.e. for InyokaEdit."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="linkmap.csv"'

    writer = csv.writer(response)
    rows = Linkmap.objects.values_list('token', 'url')
    writer.writerows(rows)

    return response
