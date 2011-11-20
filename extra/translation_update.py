#!/usr/bin/env python

"""Fetches translations from Transifex and updates the local .po files"""

from getpass import getpass
import json
import os
from urllib import urlopen, urlretrieve

LANGUAGES = ['de_DE']
BASE_URL = 'http://www.transifex.net/api/2/project/inyoka'

# I guess the following three lines can be done much nicer, but dunno how
abs_path = os.path.abspath(__file__)
extra_path = os.path.split(abs_path)[0]
base_path = os.path.abspath('/'.join([extra_path, '..', 'inyoka']))

print 'Transifex requires an authentication to use its API. Please type ' \
      'in your login credentials below. They will not be saved and only be ' \
      'used to fetch the latest translations from Transifex.'
print
resources = json.load(urlopen('/'.join([BASE_URL, 'resources'])))
for resource in resources:
    app = resource['slug']
    for language in LANGUAGES:
        app_path = '/'.join([base_path, app]) if app != 'global' else base_path
        file_path = '/'.join([app_path, 'locale', language, 'LC_MESSAGES',
                             'django.po'])
        url = '/'.join([BASE_URL, 'resource', app, 'translation', language]) + '?file'
        dir_path = os.path.split(file_path)[0]
        if not os.path.exists(dir_path):
            os.makedirs(dirpath)
        print 'Downloading "{0}"'.format(url)
        urlretrieve(url, file_path)

print 'Done, don\'t forget to run python manage.py compilemessages'
