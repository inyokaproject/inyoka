# -*- coding: utf-8 -*-
"""
    inyoka.portal.forms
    ~~~~~~~~~~~~~~~~~~~

    Various forms for the portal.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import datetime
import Image
from django import forms
from django.core.validators import EMPTY_VALUES
from django.utils.safestring import mark_safe
from django.db.models import Count

from inyoka.forum.constants import SIMPLE_VERSION_CHOICES
from inyoka.utils.user import is_valid_username, normalize_username
from inyoka.utils.dates import TIMEZONES
from inyoka.utils.urls import href, is_safe_domain
from inyoka.utils.forms import CaptchaField, DateTimeWidget, \
                               HiddenCaptchaField, EmailField, JabberField
from inyoka.utils.local import current_request
from inyoka.utils.html import escape, cleanup_html
from inyoka.utils.storage import storage
from inyoka.utils.sessions import SurgeProtectionMixin
from inyoka.portal.user import User, UserData, Group
from inyoka.portal.models import StaticPage, StaticFile
from inyoka.wiki.parser import validate_signature, SignatureError

#: Some constants used for ChoiceFields
NOTIFY_BY_CHOICES = (
    ('mail', 'E-Mail'),
    ('jabber', 'Jabber'),
)

NOTIFICATION_CHOICES = (
    ('topic_move', 'Verschieben eines abonnierten Themas'),
    ('topic_split', 'Aufteilen eines abonnierten Themas'),
    ('pm_new', 'Neuer privater Nachricht')
)


class LoginForm(forms.Form):
    """Simple form for the login dialog"""
    username = forms.CharField(label='Benutzername, E-Mail-Adresse oder OpenID',
        help_text=u'Informationen zu OpenID findest du in der deutschen Wikipedia: '
                  u'<a href="http://de.wikipedia.org/wiki/OpenID">OpenID</a>',
        widget=forms.TextInput(attrs={'tabindex': '1'}))
    password = forms.CharField(label='Passwort', required=False,
        widget=forms.PasswordInput(render_value=False, attrs={'tabindex': '1'}),
        help_text=u'Lasse dieses Feld leer wenn du OpenID benutzt!',)
    permanent = forms.BooleanField(label='Eingeloggt bleiben',
        required=False, widget=forms.CheckboxInput(attrs={'tabindex':'1'}))

    def clean(self):
        data = self.cleaned_data
        if 'username' in data and not (data['username'].startswith('http://') or \
         data['username'].startswith('https://')) and data['password'] == '':
            msg = 'Dieses Feld ist zwingend erforderlich'
            self._errors['password'] = self.error_class([msg])
        return data


class OpenIDConnectForm(forms.Form):
    username = forms.CharField(label='Benutzername')
    password = forms.CharField(label='Passwort',
        widget=forms.PasswordInput(render_value=False),
        required=True)


class RegisterForm(forms.Form):
    """
    Form for registering a new user account.

    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.
    The user also needs to confirm our terms of usage and there are some
    techniques for bot catching included e.g a CAPTCHA and a hidden captcha
    for bots that just fill out everything.
    """
    username = forms.CharField(label='Benutzername', max_length=20)
    email = EmailField(label='E-Mail', help_text=u'Wir benötigen deine '
        u'E-Mail-Adresse, um dir ein neues Passwort zu schicken, falls du '
        u'es vergessen haben solltest. Sie ist für andere Benutzer nicht '
        u'sichtbar. ubuntuusers.de <a href="%s">garantiert</a>, dass sie '
        u'nicht weitergegeben wird.' % href('portal', 'datenschutz'))
    password = forms.CharField(label='Passwort',
        widget=forms.PasswordInput(render_value=False))
    confirm_password = forms.CharField(label=u'Passwortbestätigung',
        widget=forms.PasswordInput(render_value=False))
    captcha = CaptchaField(label='CAPTCHA')
    hidden_captcha = HiddenCaptchaField(required=False)
    terms_of_usage = forms.BooleanField()

    def clean_username(self):
        """
        Validates that the username is alphanumeric and is not already
        in use.
        """
        username = self.cleaned_data['username']
        if not is_valid_username(username):
            raise forms.ValidationError(
                u'Dein Benutzername enthält nicht benutzbare Zeichen; es sind nur alphanumerische Zeichen sowie „-“ und „ “ erlaubt.'
            )
        try:
            User.objects.get(username)
        except User.DoesNotExist:
            # To bad we had to change the user regex…,  we need to rename users fast…
            count = User.objects.filter(username__contains=username.replace(' ', '%')) \
                                .aggregate(user_count=Count('username'))['user_count']
            if count == 0:
                return username

        raise forms.ValidationError(
            u'Der Benutzername ist leider schon vergeben. '
            u'Bitte wähle einen anderen.'
        )

    def clean(self):
        """
        Validates that the two password inputs match.
        """
        if 'password' in self.cleaned_data and 'confirm_password' in self.cleaned_data:
            if self.cleaned_data['password'] == self.cleaned_data['confirm_password']:
                return self.cleaned_data
            raise forms.ValidationError(
                u'Das Passwort muss mit der Passwortbestätigung übereinstimmen!'
            )
        else:
            raise forms.ValidationError(
                u'Du musst ein Passwort und eine Passwortbestätigung angeben!'
            )

    def clean_terms_of_usage(self):
        """Validates that the user agrees our terms of usage"""
        if self.cleaned_data.get('terms_of_usage', False):
            return True
        raise forms.ValidationError(
            u'Du musst unsere Hinweise zur Nutzung von ubuntuusers.de '
            u'gelesen haben und bestätigen!'
        )

    def clean_email(self):
        """
        Validates if the required field `email` contains
        a non existing mail address.
        """
        exists = User.objects.filter(email__iexact=self.cleaned_data['email'])\
                             .exists()
        if exists:
            raise forms.ValidationError(mark_safe(
                u'Die angegebene E-Mail-Adresse wird bereits benutzt!'
                u' Falls du dein Passwort vergessen hast, kannst du es '
                u'<a href="%s">wiederherstellen lassen</a>' % escape(
                    href('portal', 'lost_password'))))
        return self.cleaned_data['email']


class LostPasswordForm(forms.Form):
    """
    Form for the lost password form.

    It's similar to the register form and uses
    a hidden and a visible image CAPTCHA too.
    """
    username = forms.CharField(label=u'Benutzername oder E-Mail-Adresse')
    captcha = CaptchaField(label='CAPTCHA')
    hidden_captcha = HiddenCaptchaField(required=False)

    def clean_username(self):
        data = super(LostPasswordForm, self).clean()
        if 'username' in data and '@' in data['username']:
            try:
                self.user = User.objects.get(email=data['username'])
            except User.DoesNotExist:
                raise forms.ValidationError(
                    u'Einen Benutzer mit der E-Mail-Adresse „%s“ '
                    u'gibt es nicht!' % data['username']
                )
        else:
            try:
                self.user = User.objects.get(data['username'])
            except User.DoesNotExist:
                raise forms.ValidationError(
                    u'Der Benutzer „%s” existiert nicht!' % data['username']
                )


class SetNewPasswordForm(forms.Form):
    username = forms.CharField(widget=forms.HiddenInput)
    new_password_key = forms.CharField(widget=forms.HiddenInput)
    password = forms.CharField(label='Neues Passwort',
                               widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='Neues Passwort (Bestätigung)',
                                       widget=forms.PasswordInput)

    def clean(self):
        data = super(SetNewPasswordForm, self).clean()
        if 'password' not in data or 'password_confirm' not in data or \
           data['password'] != data['password_confirm']:
            raise forms.ValidationError(u'Die Passwörter stimmen nicht '
                                        u'überein!')
        try:
            data['user'] = User.objects.get(self['username'].data,
                               new_password_key=self['new_password_key'].data)
        except User.DoesNotExist:
            raise forms.ValidationError(u'Der Benutzer konnte nicht gefunden '
                                        u'werden oder der Bestätigungskey '
                                        u'ist nicht mehr gültig.')
        return data


class ChangePasswordForm(forms.Form):
    """Simple form for changing the password."""
    old_password = forms.CharField(label='Altes Passwort',
                                   widget=forms.PasswordInput)
    new_password = forms.CharField(label='Neues Passwort',
                                   widget=forms.PasswordInput)
    new_password_confirm = forms.CharField(
                                   label=u'Neues Passwort (Bestätigung)',
                                   widget=forms.PasswordInput)


class UserCPSettingsForm(forms.Form):
    """
    Form used for the user control panel – dialog.
    """
    notify = forms.MultipleChoiceField(
        label='Benachrichtigen per', required=False,
        choices=NOTIFY_BY_CHOICES,
        widget=forms.CheckboxSelectMultiple)
    notifications = forms.MultipleChoiceField(
        label=u'Benachrichtigen bei', required=False,
        choices=NOTIFICATION_CHOICES,
        widget=forms.CheckboxSelectMultiple)
    ubuntu_version = forms.MultipleChoiceField(
        label='Benachrichtigung bei neuen Topics mit bestimmter Ubuntu Version',
        required=False, choices=SIMPLE_VERSION_CHOICES,
        widget=forms.CheckboxSelectMultiple)
    timezone = forms.ChoiceField(label='Zeitzone', required=True,
        choices=zip(TIMEZONES, TIMEZONES))
    hide_profile = forms.BooleanField(label='Online-Status verstecken',
                                      required=False)
    hide_avatars = forms.BooleanField(label='Avatare ausblenden',
                                      required=False)
    hide_signatures = forms.BooleanField(label='Signaturen ausblenden',
                                         required=False)
    autosubscribe = forms.BooleanField(required=False,
                        label='Thema bei Antwort automatisch abonnieren')
    show_preview = forms.BooleanField(required=False,
        label='Anhang-Vorschau im Forum aktivieren')
    show_thumbnails = forms.BooleanField(required=False,
        label='Bilder-Vorschau ebenfalls aktivieren',
        help_text='automatisch deaktiviert, wenn „Anhang-Vorschau“ deaktiviert ist')
    highlight_search = forms.BooleanField(required=False,
        label='Suchwörter hervorheben',
        help_text='Suchwörter werden in gelber Farbe hervorgehoben')
    mark_read_on_logout = forms.BooleanField(required=False,
        label=u'Automatisch alle Foren beim Abmelden als gelesen markieren')


    def clean_notify(self):
        data = self.cleaned_data['notify']
        if u'jabber' in data:
            if not current_request.user.jabber:
                raise forms.ValidationError(mark_safe(u'Du musst eine gültige Jabber '
                    u'Adresse <a href="%s">angeben</a>, um unseren Jabber '
                    u'Service nutzen zu können.' % escape(href(
                        'portal', 'usercp', 'profile'))))
        return data


class UserCPProfileForm(forms.Form):

    avatar = forms.ImageField(label='Avatar', required=False)
    delete_avatar = forms.BooleanField(label=u'Avatar löschen', required=False)
    use_gravatar = forms.BooleanField(label=u'Gravatar benutzen', required=False,
        help_text=u'Es wird anstelle von dem hier eingetragenen Avatar dein '
                  u'<a href="http://gravatar.com">Gravatar</a> benutzt.<br />'
                  u'Es wird deine hier eingestellte E-Mail Adresse für die '
                  u'Verknüpfung zu Gravatar benutzt.')
    email = EmailField(label='E-Mail', required=True)
    jabber = JabberField(label='Jabber', required=False)
    icq = forms.IntegerField(label='ICQ', required=False,
                             min_value=1, max_value=1000000000)
    msn = forms.CharField(label='MSN Messenger', required=False)
    aim = forms.CharField(label='AIM', required=False, max_length=25)
    yim = forms.CharField(label='Yahoo Instant Messenger', required=False,
                         max_length=25)
    skype = forms.CharField(label='Skype', required=False, max_length=25)
    wengophone = forms.CharField(label='WengoPhone', required=False,
                                 max_length=25)
    sip = forms.CharField(label='SIP', required=False, max_length=25)
    show_email = forms.BooleanField(required=False)
    show_jabber = forms.BooleanField(required=False)
    signature = forms.CharField(widget=forms.Textarea, label='Signatur',
                               required=False)
    coordinates = forms.CharField(label='Koordinaten (Breite, Länge)',
                                  required=False, help_text=u'''
    Probleme beim bestimmen der Koordinaten?
    <a href="http://www.fallingrain.com/world/">Suche einfach deinen Ort</a>
    und übernimm die Koordinaten.''')
    location = forms.CharField(label='Wohnort', required=False, max_length=50)
    occupation = forms.CharField(label='Beruf', required=False, max_length=50)
    interests = forms.CharField(label='Interessen', required=False,
                                max_length=100)
    website = forms.URLField(label='Webseite', required=False)
    launchpad = forms.CharField(label=u'Launchpad-Benutzername', required=False,
                                max_length=50)
    gpgkey = forms.RegexField('^(0x)?[0-9a-f]{8}$(?i)', label=u'GPG-Schlüssel',
                 max_length=10, required=False, help_text=u'''
    Hier kannst du deinen GPG-Key eintragen. Näheres zu diesem Thema
    erfährst du <a href="http://wiki.ubuntuusers.de/GnuPG/Web_of_Trust">im
    Wiki</a>.''')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(UserCPProfileForm, self).__init__(*args, **kwargs)

    def clean_gpgkey(self):
        gpgkey = self.cleaned_data.get('gpgkey', '').upper()
        if gpgkey.startswith('0X'):
            gpgkey = gpgkey[2:]
        return gpgkey

    def clean_signature(self):
        signature = self.cleaned_data.get('signature', '')
        try:
            validate_signature(signature)
        except SignatureError, exc:
            raise forms.ValidationError(exc.message)
        return signature

    def clean_coordinates(self):
        coords = self.cleaned_data.get('coordinates', '').strip()
        if not coords:
            return None
        try:
            coords = [float(x.strip()) for x in coords.split(',')]
            if len(coords) != 2:
                raise forms.ValidationError(u'Koordinaten müssen im Format '
                                            u'"Länge, Breite" angegeben werden.')
            lat, long = coords
        except ValueError:
            raise forms.ValidationError(u'Koordinaten müssen Dezimalzahlen sein.')
        if not -90 < lat < 90:
            raise forms.ValidationError(u'Längenmaße müssen zwischen -90 und 90 sein.')
        if not -180 < long < 180:
            raise forms.ValidationError(u'Breitenmaße müssen zwischen -180 und 180 sein.')
        return lat, long

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if not email:
            raise forms.ValidationError(u'Keine Email-Adresse angegeben!')
        try:
            other_user = User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        else:
            if other_user.id != self.user.id:
                raise forms.ValidationError(u'Diese E-Mail-Adresse wird schon verwendet!')
            return email

    def clean_avatar(self):
        """
        Keep the user form setting avatar to a too big size.
        """
        data = self.cleaned_data
        if data['avatar'] is None:
            return
        if data['avatar'] is False:
            return False

        st = int(storage.get('max_avatar_size', 0))
        if st and data['avatar'].size > st * 1024:
            raise forms.ValidationError(
                u'Der von dir ausgewählte Avatar konnte nicht '
                u'hochgeladen werden, da er zu groß ist. Bitte '
                u'wähle einen anderen Avatar.')
        try:
            image = Image.open(data['avatar'])
        finally:
            data['avatar'].seek(0)
        max_size = (
            int(storage.get('max_avatar_width', 0)),
            int(storage.get('max_avatar_height', 0)))
        if any(length > max_length for max_length, length in zip(max_size, image.size)):
            raise forms.ValidationError(
                u'Der von dir ausgewählte Avatar konnte nicht '
                u'hochgeladen werden, da er zu groß ist. Bitte '
                u'wähle einen anderen Avatar.')
        return data['avatar']

    def clean_openid(self):
        if self.cleaned_data['openid'] in EMPTY_VALUES:
            return
        openid = self.cleaned_data['openid']
        if UserData.objects.filter(key='openid', value=openid)\
                           .exclude(user=self.user).count():
            raise forms.ValidationError(u'Diese OpenID ist bereits in '
                                        u'Verwendung')
        return openid



class EditUserProfileForm(UserCPProfileForm):
    username = forms.CharField(label=u'Benutzername', max_length=30)
    member_title = forms.CharField(label=u'Benutzer-Titel', required=False)

    def clean_username(self):
        """
        Validates that the username is alphanumeric and is not already
        in use.
        """
        data = self.cleaned_data
        username = data['username']
        if not is_valid_username(username):
            raise forms.ValidationError(u'Der Benutzername enthält '
                                        u'nicht benutzbare Zeichen')
        if (self.user.username != username and
            User.objects.filter(username=username).exists()):
                raise forms.ValidationError(
                    u'Ein Benutzer mit diesem Namen existiert bereits')
        return username


class EditUserGroupsForm(forms.Form):
    primary_group = forms.CharField(label=u'Primäre Gruppe', required=False,
        help_text=u'Wird unter anderem für das anzeigen des Team-Icons verwendet')


class CreateUserForm(forms.Form):
    username = forms.CharField(label=u'Benutzername', max_length=30)
    password = forms.CharField(label=u'Passwort',
        widget=forms.PasswordInput(render_value=False))
    confirm_password = forms.CharField(label=u'Passwort (Wiederholung)',
        widget=forms.PasswordInput(render_value=False))
    email = EmailField(label=u'E-Mail')
    authenticate = forms.BooleanField(label=u'Autentifizieren', initial=True,
        required=False, help_text=(u'Der Benutzer bekommt eine '
            u'Bestätigungsmail zugesendet und wird als inaktiv erstellt.'))

    def clean_username(self):
        """
        Validates that the username is alphanumeric and is not already
        in use.
        """
        data = self.cleaned_data
        username = data['username']
        if not is_valid_username(username):
            raise forms.ValidationError(u'Der Benutzername enthält '
                                        u'nicht benutzbare Zeichen')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                u'Der Benutzername ist leider schon vergeben. '
                u'Bitte wähle einen anderen.')
        return username

    def clean_confirm_password(self):
        """
        Validates that the two password inputs match.
        """
        data = self.cleaned_data
        if 'password' in data and 'confirm_password' in data:
            if data['password'] == data['confirm_password']:
                return data['confirm_password']
            raise forms.ValidationError(
                u'Das Passwort muss mit der Paswortbestätigung übereinstimmen!'
            )
        else:
            raise forms.ValidationError(
                u'Du musst ein Passwort und eine Passwortbestätigung angeben!'
            )

    def clean_email(self):
        """
        Validates if the required field `email` contains
        a non existing mail address.
        """
        if 'email' in self.cleaned_data:
            if User.objects.filter(email=self.cleaned_data['email']).exists():
                raise forms.ValidationError(
                    u'Die angegebene E-Mail-Adresse wird bereits benutzt!')
            return self.cleaned_data['email']
        else:
            raise forms.ValidationError(
                u'Du musst eine E-Mail-Adresse angeben!')


class EditUserStatusForm(forms.Form):
    status = forms.ChoiceField(label=u'Status', required=False,
                                   choices=enumerate([
                                       u'noch nicht aktiviert',
                                       u'aktiv',
                                       u'gebannt',
                                       u'hat sich selbst gelöscht']))
    banned_until = forms.DateTimeField(label=u'Automatisch entsperren', required=False,
        widget=DateTimeWidget,
        help_text='leer lassen, um dauerhaft zu bannen (wirkt nur wenn Status=gebannt)',
        localize=True)

    def clean_banned_until(self):
        """
        Keep the user from setting banned_until if status is not banned.
        This is to avoid confusion because this was previously possible.
        """
        data = self.cleaned_data
        if data['banned_until'] is None:
            return
        if data['status'] not in (2, '2'):
            raise forms.ValidationError(
                u'Der Benutzer ist gar nicht gebannt'
            )
        if data['banned_until'] < datetime.datetime.utcnow():
            raise forms.ValidationError(
                u'Der Zeitpunkt liegt in der Vergangenheit'
            )
        return data['banned_until']


class EditUserPasswordForm(forms.Form):
    new_password = forms.CharField(label=u'Neues Passwort',
        required=False, widget=forms.PasswordInput(render_value=False))
    confirm_password = forms.CharField(label=u'Neues Passwort (Wiederholung)',
        required=False, widget=forms.PasswordInput(render_value=False))

    def clean_confirm_password(self):
        """
        Validates that the two password inputs match.
        """
        data = self.cleaned_data
        if 'new_password' in data and 'confirm_password' in data:
            if data['new_password'] == data['confirm_password']:
                return data['confirm_password']
            raise forms.ValidationError(
                u'Das Passwort muss mit der Passwortbestätigung übereinstimmen!'
            )
        else:
            raise forms.ValidationError(
                u'Du musst ein Passwort und eine Passwortbestätigung angeben!'
            )


class EditUserPrivilegesForm(forms.Form):
    permissions = forms.MultipleChoiceField(label=u'Privilegien',
                                            required=False)


class UserMailForm(forms.Form):
    text = forms.CharField(label=u'Text',
        widget=forms.Textarea(),
        help_text=u"""Die Nachricht wird als „reiner Text“ abgeschickt. Dein
Benutzername wird in der Mail als Absender vermerkt."""
    )


class EditGroupForm(forms.Form):
    name = forms.CharField(label=u'Gruppenname', max_length=80)
    is_public = forms.BooleanField(label=u'Öffentlich', required=False)
    permissions = forms.MultipleChoiceField(label=u'Privilegien',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'permission'}),
        required=False)
    forum_privileges = forms.MultipleChoiceField(label=u'Forumsprivilegien',
                                                 required=False)
    icon = forms.ImageField(label=u'Team-Icon', required=False)
    delete_icon = forms.BooleanField(label=u'Team-Icon löschen', required=False)
    import_icon_from_global = forms.BooleanField(label=u'Globales Team-Icon benutzen',
        required=False)


class CreateGroupForm(EditGroupForm):

    def clean_name(self):
        """Validates that the name is alphanumeric and is not already in use."""

        data = self.cleaned_data
        if 'name' in data:
            try:
                name = normalize_username(data['name'])
            except ValueError:
                raise forms.ValidationError(u'Der Gruppenname enthält '
                                            u'nicht benutzbare Zeichen')
            if Group.objects.filter(name=name).exists():
                raise forms.ValidationError(
                    u'Der Gruppename ist leider schon vergeben. '
                    u'Bitte wähle einen anderen.')
            return name
        else:
            raise forms.ValidationError(u'Du musst einen Gruppennamen angeben!')


class PrivateMessageForm(forms.Form):
    """Form for writing a new private message"""
    recipient = forms.CharField(label=u'Empfänger', required=False,
        help_text="Mehrere Namen mit Semikolon getrennt eingeben.")
    group_recipient = forms.CharField(label=u'Gruppen', required=False,
        help_text="Mehrere Gruppen mit Semikolon getrennt eingeben.")
    subject = forms.CharField(label=u'Betreff',
                              widget=forms.TextInput(attrs={'size': 50}))
    text = forms.CharField(label=u'Text', widget=forms.Textarea)

    def clean(self):
        d = self.cleaned_data
        if 'recipient' in d and 'group_recipient' in d:
            if not d['recipient'].strip() and not d['group_recipient'].strip():
                raise forms.ValidationError(u'Mindestens einen Empfänger angeben.')
        return self.cleaned_data

class PrivateMessageFormProtected(SurgeProtectionMixin, PrivateMessageForm):
    source_protection_timeout = 60 * 5


class DeactivateUserForm(forms.Form):
    """Form for the user control panel -- deactivate_user view."""
    password_confirmation = forms.CharField(widget=forms.PasswordInput)


class SubscriptionForm(forms.Form):
    #: this is a list of integers of the subscriptions
    select = forms.MultipleChoiceField()


class PrivateMessageIndexForm(forms.Form):
    #: this is a list of integers of the pms that should get deleted
    delete = forms.MultipleChoiceField()


class UserErrorReportForm(forms.Form):
    title = forms.CharField(label='kurze Beschreibung', max_length=50,
                            widget=forms.TextInput(attrs={'size':50}))
    text = forms.CharField(label=u'ausführliche Beschreibung',
                           widget=forms.Textarea(attrs={'rows': 3}))
    url = forms.URLField(widget=forms.HiddenInput, required=False,
                         label=u'Adresse der Seite, auf die sich das Ticket bezieht')

    def clean_url(self):
        data = self.cleaned_data
        if data.get('url') and not is_safe_domain(self.cleaned_data['url']):
            raise forms.ValidationError(u'Ungültige URL')
        return self.cleaned_data['url']


def _feed_count_cleanup(n):
    COUNTS = (10, 20, 30, 50)
    if n in COUNTS:
        return n
    if n < COUNTS[0]:
        return COUNTS[0]
    for i in range(len(COUNTS)):
        if n < COUNTS[i]:
            return n - COUNTS[i-1] < COUNTS[i] - n and COUNTS[i-1] or COUNTS[i]
    return COUNTS[-1]


class FeedSelectorForm(forms.Form):
    count = forms.IntegerField(initial=10,
                widget=forms.TextInput(attrs={'size': 2, 'maxlength': 3,
                                              'class': 'feed_count'}),
                label=u'Anzahl der Einträge im Feed',
                help_text=u'Die Anzahl wird gerundet, um die Serverlast '
                          u'gering zu halten')
    mode = forms.ChoiceField(initial='short',
        choices=(('full',  u'Ganzer Beitrag'),
                 ('short', u'Nur Einleitung'),
                 ('title', u'Nur Titel')),
        widget=forms.RadioSelect(attrs={'class':'radioul'}))

    def clean(self):
        data = self.cleaned_data
        data['count'] = _feed_count_cleanup(data.get('count', 20))
        return data


class ForumFeedSelectorForm(FeedSelectorForm):
    component = forms.ChoiceField(initial='forum',
        choices=(('*', u''), ('forum', u''), ('topic', u'')))
    forum = forms.ChoiceField(required=False)

    def clean_forum(self):
        data = self.cleaned_data
        if data.get('component') == 'forum' and not data.get('forum'):
            raise forms.ValidationError(u'Bitte auswählen')
        return data['forum']


class IkhayaFeedSelectorForm(FeedSelectorForm):
    category = forms.ChoiceField(label=u'Kategorie')


class PlanetFeedSelectorForm(FeedSelectorForm):
    pass


class WikiFeedSelectorForm(FeedSelectorForm):
    #: `mode` is never used but needs to be overwritten because of that.
    mode = forms.ChoiceField(required=False)
    page = forms.CharField(label=u'Seitenname', required=False,
                           help_text=(u'Wenn nicht angegeben, werden die letzten '
                                 u'Änderungen angezeigt'))


class EditStaticPageForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EditStaticPageForm, self).__init__(*args, **kwargs)
        self.fields['key'].required = False

    class Meta:
        model = StaticPage


class EditFileForm(forms.ModelForm):
    class Meta:
        model = StaticFile
        exclude = ['identifier']

    def save(self, commit=True):
        instance = super(EditFileForm, self).save(commit=False)
        instance.identifier = instance.file.name.rsplit('/', 1)[-1]
        if commit:
            instance.save()
        return instance


class ConfigurationForm(forms.Form):
    global_message = forms.CharField(label=u'Globale Nachricht',
        widget=forms.Textarea(attrs={'rows': 3}), required=False,
        help_text = u'Diese Nachricht wird auf allen Seiten über dem Inhalt '
                    u'angezeigt. Um sie zu deaktivieren, lasse das Feld leer. '
                    u'Muss valides XHTML sein.')
    blocked_hosts = forms.CharField(label=u'Verbotene Hosts für E-Mail-Adressen',
        widget=forms.Textarea(attrs={'rows': 3}), required=False,
        help_text = u'Benutzer können keine E-Mail-Adressen von diesen Hosts '
                    u'zum Registrieren verwenden.')
    team_icon = forms.ImageField(label=u'Globales Teamicon', required=False,
        help_text=u'Beachte bitte untenstehende Angaben zu der Maximalgröße')
    max_avatar_width = forms.IntegerField(min_value=1)
    max_avatar_height = forms.IntegerField(min_value=1)
    max_avatar_size = forms.IntegerField(min_value=0)
    max_signature_length = forms.IntegerField(min_value=1,
        label=u'Maximale Signaturlänge')
    max_signature_lines = forms.IntegerField(min_value=1,
        label=u'Maximale Zeilenanzahl in Signatur')
    get_ubuntu_link = forms.URLField(required=False,
        label=u'Der Downloadlink für die Startseite')
    get_ubuntu_description = forms.CharField(label=u'Beschreibung des Links')
    wiki_newpage_template = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'rows': 5}),
        label=u'Standardtext beim Anlegen neuer Wiki-Seiten')
    wiki_newpage_root = forms.CharField(required=False,
        label=u'Unter welcher Wikiseite sollen neue Seiten erstellt werden?')
    wiki_newpage_infopage = forms.CharField(required=False,
        label=u'Infoseite für neue Seiten.',
        help_text=u'Infoseite auf die ein "erstellen" Link zeigen soll.'
                  u' Wenn leer wird ein Standardlink benutzt.')
    team_icon_width = forms.IntegerField(min_value=1, required=False)
    team_icon_height = forms.IntegerField(min_value=1, required=False)
    license_note = forms.CharField(required=False, label=u'Lizenzhinweis',
                                   widget=forms.Textarea(attrs={'rows': 2}))

    def clean_global_message(self):
        return cleanup_html(self.cleaned_data.get('global_message', ''))


class EditStyleForm(forms.Form):
    styles = forms.CharField(label=u'Styles', widget=forms.Textarea(
                             attrs={'rows': 20}), required=False)


class SearchForm(forms.Form):
    q = forms.CharField(label='Suche', max_length=100,
            widget=forms.TextInput(attrs={'placeholder': 'Suche',
                                          'autocomplete':'off',
                                          'spellcheck':'off'}))
