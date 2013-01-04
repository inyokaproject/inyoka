# -*- coding: utf-8 -*-
"""
    inyoka.utils.forms
    ~~~~~~~~~~~~~~~~~~

    This file contains extensions for the django forms like special form
    fields.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys
import pytz
from hashlib import md5
from random import randrange

from django import forms
from django.conf import settings
from django.core import validators
from django.forms.widgets import Input
from django.utils.translation import ugettext as _

from inyoka.portal.user import User
from inyoka.markup import parse, StackExhaused
from inyoka.utils.dates import datetime_to_timezone, get_user_timezone
from inyoka.utils.jabber import may_be_valid_jabber
from inyoka.utils.local import current_request
from inyoka.utils.mail import is_blocked_host
from inyoka.utils.text import slugify
from inyoka.utils.urls import href
from inyoka.utils.storage import storage


def clear_surge_protection(request, form):
    """Clean errors in parent form so that submitting inherited forms
    don't raise any errors.

    This function also cleanup the surge surge protection timer so
    that we get no nasty hickups by just submitting an inherited form
    and sending the whole form afterwards.
    """
    # Cleanup errors in parent form if the main form was not send.
    if request.method == 'POST' and not 'send' in request.POST:
        form.errors.clear()
        if 'sp' in request.session:
            del request.session['sp']


def validate_empty_text(value):
    if not value.strip():
        raise forms.ValidationError(_(u'Text must not be empty'), code='invalid')
    return value


def validate_signature(signature):
    """Parse a signature and check if it's valid."""
    def _walk(node):
        if node.is_container:
            for n in node.children:
                _walk(n)
        if not node.allowed_in_signatures:
            raise forms.ValidationError(_(u'Your signature contains illegal elements'))
        return node
    try:
        text = _walk(parse(signature, True, False)).text.strip()
    except StackExhaused:
        raise forms.ValidationError(_(u'Your signature contains too many nested elements'))
    sig_len = int(storage.get('max_signature_length', -1))
    sig_lines = int(storage.get('max_signature_lines', -1))
    if sig_len >= 0 and len(text) > sig_len:
        raise forms.ValidationError(
            _(u'Your signature is too long, only %(length)s characters '
              u'allowed') % {'length': sig_len})
    if sig_lines >= 0 and len(text.splitlines()) > sig_lines:
        raise forms.ValidationError(
            _(u'Your signature can only contain up to %(num)d lines') % {
                'num': sig_lines})


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
        if isinstance(data, basestring):
            return data
        elif data is None:
            return ''
        elif isinstance(data, User):
            return data.username
        else:
            return User.objects.get(data).username

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return
        try:
            return User.objects.get(username=value)
        except (User.DoesNotExist, ValueError):
            raise forms.ValidationError(_(u'This user does not exist'))


class DateTimeWidget(Input):
    input_type = 'text'
    value_type = 'datetime'

    def render(self, name, value, attrs=None):
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
        if isinstance(data, basestring):
            return data
        datetime = super(DateTimeField, self).prepare_value(data)
        return datetime_to_timezone(datetime).replace(tzinfo=None)

    def clean(self, value):
        datetime = super(DateTimeField, self).clean(value)
        if not datetime:
            return
        datetime = get_user_timezone().localize(datetime) \
                       .astimezone(pytz.utc).replace(tzinfo=None)
        return datetime


class StrippedCharField(forms.CharField):
    default_validators = [validate_empty_text]


class EmailField(forms.EmailField):

    def clean(self, value):
        value = super(EmailField, self).clean(value)
        value = value.strip()
        if is_blocked_host(value):
            raise forms.ValidationError(_(u'The entered e-mail address belongs to a '
                u'e-mail provider we had to block because of SPAM problems. Please '
                u'choose another e-mail address'))
        return value


class JabberField(forms.CharField):

    def clean(self, value):
        if not value:
            return
        value = value.strip()
        if not may_be_valid_jabber(value):
            raise forms.ValidationError(_(u'The entered Jabber address is invalid. '
                u'Please check your input.'))
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
                _(u'You have entered an invisible field '
                  u'and were therefore classified as a bot.'))


class ImageCaptchaWidget(Input):
    input_type = 'text'

    def render(self, name, value, attrs=None):
        input_ = Input.render(self, name, u'', attrs)
        img = '<img src="%s" class="captcha" alt="%s" />' % (
              href('portal', __service__='portal.get_captcha',
                   rnd=randrange(1, sys.maxint)), _('CAPTCHA'))
        text = '%s:' % _('Please type in the code from the graphic above')
        input_tag = '%s <input type="submit" name="renew_captcha" value="%s" />' % (
                    input_, _('Generate new code'))
        return '<br />'.join([img, text, input_tag])


class ImageCaptchaField(forms.Field):
    widget = ImageCaptchaWidget

    def __init__(self, only_anonymous=False, *args, **kwargs):
        self.only_anonymous = only_anonymous
        forms.Field.__init__(self, *args, **kwargs)

    def clean(self, value):
        if current_request.user.is_authenticated() and self.only_anonymous:
            return True
        value = super(ImageCaptchaField, self).clean(value)
        solution = current_request.session.get('captcha_solution')
        if value:
            h = md5(settings.SECRET_KEY)
            if isinstance(value, unicode):
                # md5 doesn't like to have non-ascii containing unicode strings
                value = value.encode('utf-8')
            if value:
                h.update(value)
            if h.digest() == solution:
                return True
        raise forms.ValidationError(_(u'The entered CAPTCHA was incorrect.'))


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
        fields = (ImageCaptchaField(), HiddenCaptchaField())
        kwargs['required'] = False
        super(CaptchaField, self).__init__(fields, *args, **kwargs)
        fields[0].required = True # Ensure the Captcha is required.

    def compress(self, data_list):
        pass # CaptchaField doesn't have a useful value to return.
