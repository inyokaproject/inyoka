# -*- coding: utf-8 -*-
"""
    inyoka.utils.forms
    ~~~~~~~~~~~~~~~~~~

    This file contains extensions for the django forms like special form
    fields.

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re
import sys
from hashlib import md5
from random import randrange
import urllib.request, urllib.parse, urllib.error
import urllib.parse

import pytz
from django import forms
from django.conf import settings
from django.core import validators
from django.forms import MultipleChoiceField
from django.forms.widgets import Input, TextInput
from django.utils.timezone import get_current_timezone
from django.utils.translation import gettext as _

from inyoka.forum.models import Topic
from inyoka.markup.base import StackExhaused, parse
from inyoka.portal.user import User
from inyoka.utils.dates import datetime_to_timezone
from inyoka.utils.jabber import may_be_valid_jabber
from inyoka.utils.local import current_request
from inyoka.utils.mail import is_blocked_host
from inyoka.utils.sessions import SurgeProtectionMixin
from inyoka.utils.text import slugify
from inyoka.utils.urls import href


def clear_surge_protection(request, form):
    """Clean errors in parent form so that submitting inherited forms
    don't raise any errors.

    This function also cleanup the surge surge protection timer so
    that we get no nasty hickups by just submitting an inherited form
    and sending the whole form afterwards.
    """
    # Cleanup errors in parent form if the main form was not send.
    if request.method == 'POST' and 'send' not in request.POST:
        form.errors.clear()
        if 'sp' in request.session:
            if isinstance(form, SurgeProtectionMixin):
                identifier = form.get_surge_protection_identifier()
                request.session['sp'].pop(identifier, None)


def validate_empty_text(value):
    if not value.strip():
        raise forms.ValidationError(_('Text must not be empty'), code='invalid')
    return value


def validate_signature(signature):
    """Parse a signature and check if it's valid."""
    def _walk(node):
        if node.is_container:
            for n in node.children:
                _walk(n)
        if not node.allowed_in_signatures:
            raise forms.ValidationError(_('Your signature contains illegal elements'))
        return node
    try:
        text = _walk(parse(signature, True, False)).text.strip()
    except StackExhaused:
        raise forms.ValidationError(_('Your signature contains too many nested elements'))

    sig_len = int(settings.INYOKA_SIGNATURE_MAXIMUM_CHARACTERS)
    sig_lines = int(settings.INYOKA_SIGNATURE_MAXIMUM_LINES)
    if sig_len >= 0 and len(text) > sig_len:
        raise forms.ValidationError(
            _('Your signature is too long, only %(length)s characters '
              'allowed') % {'length': sig_len})
    if sig_lines >= 0 and len(text.splitlines()) > sig_lines:
        raise forms.ValidationError(
            _('Your signature can only contain up to %(num)d lines') % {
                'num': sig_lines})


def validate_gpgkey(value):
    gpgkeyRegex = re.compile('^(0x)?[0-9a-f]{40}$', re.IGNORECASE)
    trimmedValue = value.replace(' ', '')
    if not gpgkeyRegex.match(trimmedValue):
        raise forms.ValidationError(_('"%(fingerprint)s" is not a valid GPG Fingerprint.'),
                              params={'fingerprint': value})


class MultiField(forms.Field):
    """
    This field validates a bunch of values using zero, one or more fields.
    If the value is just one string, a list is created.
    """
    widget = forms.SelectMultiple

    def __init__(self, fields=(), *args, **kwargs):
        super(MultiField, self).__init__(*args, **kwargs)
        self.fields = fields

    def clean(self, value):
        """
        Validates that the value is a list or a tuple.
        """
        if not isinstance(value, (list, tuple)):
            value = [value]

        def _clean(part):
            for field in self.fields:
                part = field.clean(part)
            return part

        return [_clean(part) for part in value]


class UserField(forms.CharField):
    """
    Allows to enter a username as text and validates if the given user exists.
    """

    def prepare_value(self, data):
        """
        Returns the username from the given data.

        data can be:
        - the a basestring, then it has to be the username,
        - None, then the field is empty,
        - an user object, then the username of this user is returned or
        - an user id, then the user is fetched from the database.
        """
        if isinstance(data, str):
            return data
        elif data is None:
            return ''
        elif isinstance(data, User):
            return data.username
        else:
            # data is the user id
            return User.objects.get(pk=data).username

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return
        try:
            return User.objects.get(username__iexact=value)
        except (User.DoesNotExist, ValueError):
            raise forms.ValidationError(_('This user does not exist'))


class DateTimeWidget(Input):
    input_type = 'text'
    value_type = 'datetime'

    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        attrs['valuetype'] = self.value_type
        return Input.render(self, name, value, attrs)


class DateWidget(DateTimeWidget):
    input_type = 'text'
    value_type = 'date'


class TimeWidget(DateTimeWidget):
    input_type = 'text'
    value_type = 'time'


class DateTimeField(forms.DateTimeField):
    widget = DateTimeWidget

    def prepare_value(self, data):
        if data in validators.EMPTY_VALUES:
            return ''
        if isinstance(data, str):
            return data
        datetime = super(DateTimeField, self).prepare_value(data)
        return datetime_to_timezone(datetime).replace(tzinfo=None)

    def clean(self, value):
        datetime = super(DateTimeField, self).clean(value)
        if not datetime:
            return
        datetime = (
            get_current_timezone().localize(datetime).astimezone(pytz.utc)
            .replace(tzinfo=None))
        return datetime


class StrippedCharField(forms.CharField):
    default_validators = [validate_empty_text]


class EmailField(forms.EmailField):

    def clean(self, value):
        value = super().clean(value)
        value = value.strip()
        if is_blocked_host(value):
            raise forms.ValidationError(_('The entered e-mail address belongs to a '
                'e-mail provider we had to block because of SPAM problems. Please '
                'choose another e-mail address'))
        return value


class ForumMulitpleChoiceField(MultipleChoiceField):
    is_category = False

    def __init__(self, *args, **kwargs):
        self.is_category = kwargs.pop('is_category', lambda val: val)
        super().__init__(*args, **kwargs)


class JabberField(forms.CharField):

    def clean(self, value):
        if not value:
            return
        value = value.strip()
        if not may_be_valid_jabber(value):
            raise forms.ValidationError(_('The entered Jabber address is invalid. '
                'Please check your input.'))
        return value


class SlugField(forms.CharField):

    def clean(self, value):
        if value:
            value = slugify(value)
            return value.strip() if value else None
        return None


class HiddenCaptchaField(forms.Field):
    widget = forms.HiddenInput

    def __init__(self, *args, **kwargs):
        kwargs['required'] = False
        super(HiddenCaptchaField, self).__init__(*args, **kwargs)

    def clean(self, value):
        if not value:
            return True
        else:
            raise forms.ValidationError(
                _('You have entered an invisible field '
                  'and were therefore classified as a bot.'))


class ImageCaptchaWidget(TextInput):
    template_name = 'forms/widgets/image_captcha.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['captcha_url'] = href('portal', __service__='portal.get_captcha',
                                                rnd=randrange(1, sys.maxsize))
        return context


class ImageCaptchaField(forms.Field):
    widget = ImageCaptchaWidget

    def __init__(self, *args, **kwargs):
        forms.Field.__init__(self, *args, **kwargs)

    def clean(self, value):
        value = super(ImageCaptchaField, self).clean(value)
        solution = current_request.session.get('captcha_solution')
        if value:
            h = md5(settings.SECRET_KEY.encode())
            if value:
                h.update(value.encode())
            if h.hexdigest() == solution:
                return True
        raise forms.ValidationError(_('The entered CAPTCHA was incorrect.'))


class CaptchaWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        # The HiddenInput is a honey-pot
        widgets = ImageCaptchaWidget, forms.HiddenInput
        super(CaptchaWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        return [None, None]


class CaptchaField(forms.MultiValueField):
    widget = CaptchaWidget

    def __init__(self, *args, **kwargs):
        kwargs['required'] = True
        self.only_anonymous = kwargs.pop('only_anonymous', False)
        fields = (ImageCaptchaField(), HiddenCaptchaField())
        super(CaptchaField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        pass  # CaptchaField doesn't have a useful value to return.

    def clean(self, value):
        if current_request.user.is_authenticated and self.only_anonymous:
            return [None, None]
        value[1] = False  # Prevent being catched by validators.EMPTY_VALUES
        return super(CaptchaField, self).clean(value)


class TopicField(forms.CharField):
    label = _('URL of the topic')

    def clean(self, value):
        value = super(TopicField, self).clean(value)

        if not value:
            return None

        # Allow URL based Slugs
        try:
            slug = urllib.parse.urlparse(value)[2].split('/')[2]
        except IndexError:
            slug = urllib.parse.unquote(value)

        try:
            topic = Topic.objects.get(slug=slug)
        except Topic.DoesNotExist:
            raise forms.ValidationError(_('This topic does not exist.'))
        return topic
