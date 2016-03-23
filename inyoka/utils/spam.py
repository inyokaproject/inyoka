# -*- coding: utf-8 -*-
"""
    inyoka.utils.spam
    ~~~~~~~~~~~~~~~~~

    This module provides Akismet (https://akismet.com/) integration for Inyoka.

    :copyright: (c) 2015-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import logging

import requests
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger('inyoka.antispam')


def get_verify_key_url():
    return 'https://rest.akismet.com/1.1/verify-key'


def get_comment_check_url():
    return 'https://%s.rest.akismet.com/1.1/comment-check' % settings.INYOKA_AKISMET_KEY


def get_mark_ham_url():
    return 'https://%s.rest.akismet.com/1.1/submit-ham' % settings.INYOKA_AKISMET_KEY


def get_mark_spam_url():
    return 'https://%s.rest.akismet.com/1.1/submit-spam' % settings.INYOKA_AKISMET_KEY


verified = None


def verify_key():
    global verified
    if not settings.INYOKA_USE_AKISMET:
        return
    if verified is None:
        response = requests.post(get_verify_key_url(), {
            'blog': settings.INYOKA_AKISMET_URL,
            'key': settings.INYOKA_AKISMET_KEY,
        })
        if response.status_code == 200:
            if response.text == 'valid':
                verified = True
            elif response.text == 'invalid':
                verified = False
                debug_msg = response.headers.get(
                    'x-akismet-debug-help', 'No debug help',
                )
                logger.error('Error registering %s at Akismet: %s' % (
                    settings.INYOKA_AKISMET_URL, debug_msg,
                ))
        else:
            logger.error(
                'Unknown error registering %s at Akismet' %
                settings.INYOKA_AKISMET_URL
            )
    return verified


def is_spam(comment_content, comment_type):
    """
    Checks if the text ``comment_content`` is spam.

    :param str comment_content: The text to check for spam
    :param str comment_type: The type of posting according to
        http://blog.akismet.com/2012/06/19/pro-tip-tell-us-your-comment_type/

    :return: Returns a 2-tuple with Spam / Ham (``True``/``False``) as first
        item and ``True`` as second item iff the post should be discarded.
    """
    if not settings.INYOKA_USE_AKISMET:
        return False, False
    if not verify_key():
        # Akismet spam protection is turned on, but key verification failed
        return settings.INYOKA_AKISMET_DEFAULT_IS_SPAM, False
    data = {
        'blog': settings.INYOKA_AKISMET_URL,
        'comment_content': comment_content,
        'comment_type': comment_type,
        'user_ip': '127.0.0.1',
    }
    response = requests.post(get_comment_check_url(), data)
    if response.status_code == 200:
        if response.text == 'true':
            discard = (response.headers.get('x-akismet-pro-tip') == 'discard')
            return True, discard  # It's spam
        elif response.text == 'false':
            return False, False  # It's ham
        else:
            debug_msg = response.headers.get(
                'x-akismet-debug-help', 'No debug help',
            )
            logger.error('Error checking for spam on %s: %s' % (
                settings.INYOKA_AKISMET_URL, debug_msg,
            ))
    else:
        logger.error(
            'Unknown error checking for spam on %s' %
            settings.INYOKA_AKISMET_URL
        )
    return settings.INYOKA_AKISMET_DEFAULT_IS_SPAM, False


def mark_ham(obj, comment_content, comment_type):
    if settings.INYOKA_USE_AKISMET and verify_key():
        data = {
            'blog': settings.INYOKA_AKISMET_URL,
            'comment_content': comment_content,
            'comment_type': comment_type,
            'user_ip': '127.0.0.1',
        }
        logger.info('Submitting %s.%s with id %d as ham' % (
            obj.__class__.__module__, obj.__class__.__name__, obj.pk
        ))
        requests.post(get_mark_ham_url(), data)


def mark_spam(obj, comment_content, comment_type):
    if settings.INYOKA_USE_AKISMET and verify_key():
        data = {
            'blog': settings.INYOKA_AKISMET_URL,
            'comment_content': comment_content,
            'comment_type': comment_type,
            'user_ip': '127.0.0.1',
        }
        logger.info('Submitting %s.%s with id %d as spam' % (
            obj.__class__.__module__, obj.__class__.__name__, obj.pk
        ))
        requests.post(get_mark_spam_url(), data)


def check_form_field(form, text_field, needs_check, request, content_type):
    text = form.cleaned_data.get(text_field)
    form._spam, form._spam_discard = False, False
    if needs_check:
        form._spam, form._spam_discard = is_spam(text, content_type)
        if form._spam:
            attempts_left = block_user_if_spammer(request.user)
            msg = _(
                'Your text is considered spam and needs approval from one of '
                'the administrators. Please be patient, we will get to it as '
                'soon as possible. You have %(left)d attempts left before your '
                'account will be blocked.'
            ) % {
                'left': attempts_left,
            }
            if form._spam_discard:
                raise ValidationError(msg)
            else:
                messages.info(request, msg)
    return text


def block_user_if_spammer(user):
    cache_key = 'spam/user/%d' % user.pk
    spam_hits = cache.get(cache_key, 0) + 1
    if spam_hits >= settings.INYOKA_SPAM_COUNTER_MAX:
        user.status = user.STATUS_BANNED
        user.save(update_fields=['status'])
        logger.info(
            u'User %s (%d) hit spam counter maximum of %d. Blocked!' % (
                user.username, user.pk, settings.INYOKA_SPAM_COUNTER_MAX,
            )
        )
    else:
        cache.set(
            cache_key, spam_hits,
            timeout=settings.INYOKA_SPAM_COUNTER_TIMEOUT
        )
        logger.info(
            u'User %s (%d) tried to spam. Counter at %d of %d.' % (
                user.username, user.pk, spam_hits,
                settings.INYOKA_SPAM_COUNTER_MAX
            )
        )
    return settings.INYOKA_SPAM_COUNTER_MAX - spam_hits
