#-*- coding: utf-8 -*-
import os
import time
import logging
import shutil
import subprocess
import tempfile
import unittest

import nose
from nose.plugins import Plugin
from nose.plugins.skip import SkipTest
import pyes.exceptions
import pyes.urllib3
from django.test import TestCase
from inyoka.utils.search import autodiscover, SearchSystem


START_TIMEOUT = 15

log = logging.getLogger('nose.plugins.elastic')


class InyokaElasticPlugin(Plugin):
    """
    Starts an ElasticSearch instance to properly test our search.
    """

    enabled = True
    activation_parameter = "--with-elastic"
    name = "elastic"
    score = 80

    def __init__(self):
        Plugin.__init__(self)
        self.started = False
        self.process = None

    def start_server(self):
        self.tmpdir = tempfile.mkdtemp()
        logfile = 'elasticsearch-test.log'
        hostname = os.environ['ELASTIC_HOSTNAME']
        self.process = subprocess.Popen([
                os.path.join(
                    os.environ['ELASTIC_HOME'], 'bin', 'elasticsearch'),
                '-f',
                '-D', 'es.path.data=' + os.path.join(self.tmpdir, 'data'),
                '-D', 'es.path.work=' + os.path.join(self.tmpdir, 'work'),
                '-D', 'es.path.logs=' + os.path.join(self.tmpdir, 'logs'),
                '-D', 'es.cluster.name=inyoka.testing',
                '-D', 'es.http.port=' + hostname.split(':', 1)[-1],
                ], stdout=open(logfile, 'w'), stderr=subprocess.STDOUT)

        start = time.time()

        while True:
            time.sleep(0.5)

            with open(logfile, 'r') as f:
                contents = f.read()
                if 'started' in contents:
                    return

                if time.time() - start > START_TIMEOUT:
                    log.info('ElasticSearch could be started: :\n%s' % contents)
                    return

    def prepareTestRunner(self, test):
        """Starts the server."""
        from django.conf import settings
        if not self.started:
            # Raises an exception if not.
            settings.TEST_MODE = True
            autodiscover()
            self.start_server()
            self.started = True

    def stop_server(self):
        self.process.terminate()
        self.process.wait()

    def finalize(self, result):
        """Stops the server if necessary."""
        if self.started:
            self.stop_server()
            self.started = False
            shutil.rmtree(self.tmpdir)


class UnitTestPlugin(Plugin):
    """
    Enables unittest compatibility mode (dont test functions, only TestCase
    subclasses, and only methods that start with [Tt]est).
    """
    enabled = True
    name = "unittest"
    score = 90

    def wantClass(self, cls):
        if not issubclass(cls, unittest.TestCase):
            return False

    def wantMethod(self, method):
        if not issubclass(method.im_class, unittest.TestCase):
            return False
        if not method.__name__.lower().startswith('test'):
            return False

    def wantFunction(self, function):
        return False


class SearchTestCase(TestCase):

    def setUp(self):
        try:
            self.search = SearchSystem(os.environ['ELASTIC_HOSTNAME'])
            autodiscover()
            from inyoka.utils.search import search
            self.search.indices = search.indices
            self.search.get_connection().delete_index('_all')
        except (pyes.exceptions.ElasticSearchException,
                pyes.urllib3.MaxRetryError,
                KeyError):
            raise SkipTest('No ElasticSearch started or environment variables missing')

    def tearDown(self):
        try:
            self.search.get_connection().delete_index('_all')
        except (pyes.exceptions.ElasticSearchException,
                pyes.urllib3.MaxRetryError):
            pass

    def flush_indices(self, indices=None):
        if indices is None:
            indices = self.search.indices.iterkeys()
        if not isinstance(indices, (list, set, tuple)):
            indices = [indices]
        return self.search.get_connection().flush(indices)
