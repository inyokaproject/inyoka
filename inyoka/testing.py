#-*- coding: utf-8 -*-
import os
import time
import logging
import shutil
import subprocess
import tempfile

import nose
from nose.plugins import Plugin
import pyes.exceptions
from django.test import TestCase, TransactionTestCase


START_TIMEOUT = 15

log = logging.getLogger('nose.plugins.elastic')


def get_case_class(nose_test):
    """
    Extracts the class from the nose tests that depends on whether it's a
    method test case or a function test case.
    """
    if isinstance(nose_test.test, nose.case.MethodTestCase):
        return nose_test.test.test.im_class
    else:
        return nose_test.test.__class__


class InyokaElasticPlugin(Plugin):
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

        log.info('\n    Starting elasticsearch server')
        start = time.time()

        while True:
            time.sleep(0.5)

            with open(logfile, 'r') as f:
                contents = f.read()
                if 'started' in contents:
                    log.info(' done.\n  ')
                    return

                if time.time() - start > START_TIMEOUT:
                    log.error(' failed, log output follows:\n%s' % contents)
                    raise SystemExit

    def startTest(self, test):
        """Starts the server."""
        from django.conf import settings
        test_case = get_case_class(test)

        if not self.started and getattr(test_case, 'require_search', False):
            # Raises an exception if not.
            settings.TEST_MODE = True

            self.start_server()
            self.started = True
            setattr(test_case, 'search_plugin_started', True)

    def stop_server(self):
        self.process.terminate()
        self.process.wait()

    def stopTest(self, test):
        """Stops the server if necessary."""
        test_case = get_case_class(test)
        if self.started and \
           getattr(test_case, 'search_plugin_started', False):
            self.stop_server()
            self.started = False
            shutil.rmtree(self.tmpdir)


class SearchTestCase(TestCase):

    require_search = True

    def setUp(self):
        self.elastic = pyes.ES(os.environ['ELASTIC_HOSTNAME'])
        try:
            self.elastic.delete_index('_all')
        except pyes.exceptions.ElasticSearchException:
            pass
