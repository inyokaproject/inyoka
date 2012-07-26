#-*- coding: utf-8 -*-
"""
    inyoka.testing
    ~~~~~~~~~~~~~~

    Various utilities and helpers that improve our unittest experience.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import gc
import time
import logging
import shutil
import subprocess
import tempfile
import unittest

from copy import copy
from functools import wraps

import pyes
import pyes.exceptions

from requests.models import MaxRetryError

from django.conf import settings, UserSettingsHolder
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client
from django.utils.importlib import import_module

from inyoka.portal.user import User
from inyoka.utils.search import autodiscover, SearchSystem


START_TIMEOUT = 15


def profile_memory(func):
    # run the test 50 times.  if length of gc.get_objects()
    # keeps growing, assert false

    def profile(*args):
        gc.collect()
        samples = [0 for x in range(0, 50)]
        for x in range(0, 50):
            func(*args)
            gc.collect()
            samples[x] = len(gc.get_objects())

        for x in samples[-4:]:
            if x != samples[-5]:
                flatline = False
                break
        else:
            flatline = True

        # object count is bigger than when it started
        if not flatline and samples[-1] > samples[0]:
            for x in samples[1:-2]:
                # see if a spike bigger than the endpoint exists
                if x > samples[-1]:
                    break
            else:
                assert False, repr(samples) + " " + repr(flatline)

    return profile


class InyokaClient(Client):
    """
    In order to change the requesting host, use::

        client.defaults['HTTP_HOST'] = 'url.example.com'

    """

    def __init__(self, enforce_csrf_checks=False, host=None, **defaults):
        """Update the default request variables with ``**defaults`` and disable
        CSRF checks by default. If ``host`` is given, this host is set as
        default for further request. The user of this client is an instance of
        :class:`inyoka.portal.user.User` and :data:`INYOKA_ANONYMOUS_USER` by
        default. To change the user, call :meth:`InyokaClient.login(user)`.

        """
        super(InyokaClient, self).__init__(enforce_csrf_checks, **defaults)
        if isinstance(host, basestring):
            self.defaults['HTTP_HOST'] = host
        else:
            self.defaults['HTTP_HOST'] = settings.BASE_DOMAIN_NAME
        self.user = User.objects.get_anonymous_user()

    def login(self, **credentials):
        """Try to authenticate a user with username and password.

        :param username: The username of the :class:`~inyoka.portal.user.User`
            to login
        :param password: The password of the user to login
        :type username: string
        :type password: string
        :raise:
            User.DoesNotExist
                If the user with `username` does not exist
            :class:`~inyoka.portal.user.UserBanned`
                If the found user is banned
        :return: ``True`` in case the described user can be logged in, and is
            active, ``False`` otherwise.

        """

        username = credentials.get('username', None)
        password = credentials.get('password', None)
        assert all((username, password))

        user = User.objects.authenticate(username, password)
        if user.is_active:
            engine = import_module(settings.SESSION_ENGINE)

            # Create a fake request to store login details.
            request = HttpRequest()
            if self.session:
                request.session = self.session
            else:
                request.session = engine.SessionStore()
            user.login(request)

            # Save the session values.
            request.session.save()

            # Set the cookie to represent the session.
            session_cookie = settings.SESSION_COOKIE_NAME
            self.cookies[session_cookie] = request.session.session_key
            cookie_data = {
                'max-age': None,
                'path': '/',
                'domain': settings.SESSION_COOKIE_DOMAIN,
                'secure': settings.SESSION_COOKIE_SECURE or None,
                'expires': None,
            }
            self.cookies[session_cookie].update(cookie_data)

            return True
        else:
            return False


class SearchTestCase(TestCase):

    started = False

    @classmethod
    def setUpClass(cls):
        """Starts the server."""
        from django.conf import settings
        if not cls.started:
            # Raises an exception if not.
            settings.TEST_MODE = True
            autodiscover()
            cls.start_server()
            cls.started = True

    @classmethod
    def tearDownClass(cls):
        """Stops the server if necessary."""
        if cls.started:
            cls.stop_server()
            cls.started = False
            shutil.rmtree(cls.tmpdir)

    def setUp(self):
        try:
            self.search = SearchSystem(os.environ['ELASTIC_HOSTNAME'])
            autodiscover()
            from inyoka.utils.search import search
            self.search.indices = search.indices
            self.search.get_connection().delete_index('_all')
        except (pyes.exceptions.ElasticSearchException,
                MaxRetryError,
                KeyError):
            raise unittest.SkipTest('No ElasticSearch started or environment variables missing')

    def tearDown(self):
        try:
            self.search.get_connection().delete_index('_all')
        except (pyes.exceptions.ElasticSearchException,
                MaxRetryError):
            pass

    def flush_indices(self, indices=None):
        if indices is None:
            indices = self.search.indices.iterkeys()
        if not isinstance(indices, (list, set, tuple)):
            indices = [indices]
        return self.search.get_connection().flush(indices)

    @classmethod
    def start_server(cls):
        cls.tmpdir = tempfile.mkdtemp()
        logfile = 'elasticsearch-test.log'
        hostname = os.environ['ELASTIC_HOSTNAME']
        cls.process = subprocess.Popen([
                os.path.join(
                    os.environ['ELASTIC_HOME'], 'bin', 'elasticsearch'),
                '-f',
                '-D', 'es.path.data=' + os.path.join(cls.tmpdir, 'data'),
                '-D', 'es.path.work=' + os.path.join(cls.tmpdir, 'work'),
                '-D', 'es.path.logs=' + os.path.join(cls.tmpdir, 'logs'),
                '-D', 'es.cluster.name=inyoka.testing',
                '-D', 'es.http.port=' + hostname.split(':', 1)[-1],
                ], stdout=open(logfile, 'w'), stderr=subprocess.STDOUT)

        start = time.time()

        while True:
            time.sleep(0.1)

            with open(logfile, 'r') as f:
                contents = f.read()
                if 'started' in contents:
                    return

                if time.time() - start > START_TIMEOUT:
                    log.info('ElasticSearch could be started: :\n%s' % contents)
                    return

    @classmethod
    def stop_server(cls):
        cls.process.terminate()
        cls.process.wait()
