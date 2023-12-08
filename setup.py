"""A setuptools based setup module.

See:
for a good overview
https://packaging.python.org/guides/distributing-packages-using-setuptools/

for an example project
https://github.com/pypa/sampleproject

for more background on the metadata parameters
https://packaging.python.org/specifications/core-metadata/
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib

current_folder = pathlib.Path(__file__).parent.resolve()
long_description = (current_folder / 'README.rst').read_text(encoding='utf-8')

setup(
    name='Inyoka',
    # version defined via setup.cfg
    description='All-in-one portal software with Forum, Wiki, Planet, News and Calendar',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://inyokaproject.org/',
    author='Inyoka Team',
    classifiers=[  # see https://pypi.org/classifiers/
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Message Boards',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: News/Diary',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Wiki',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Framework :: Django',
    ],
    keywords='Forum Wiki Planet News Calendar',

    packages=find_packages(include=('inyoka*',)),
    python_requires='>=3.9, <4',
    install_requires=[
        'Django<4.0',
        'pip-tools',

        'Babel',
        'beautifulsoup4',
        'celery[redis]',
        'defusedxml',
        'django-filter',
        'django-guardian',
        'django-hosts',
        'django-redis',
        'feedparser',
        'gunicorn',
        'html5lib',
        'icalendar',
        'Jinja2',
        'lxml',
        'Pillow',
        'psycopg2',
        'Pygments',
        'python-magic',
        'python-dateutil',
        'pytz',
        'sentry-sdk',
        'requests',
        'Werkzeug<1.0'  # 1.0 removed feed support, see https://github.com/inyokaproject/inyoka/issues/1071
    ],

    extras_require={
        'dev': ['allure-behave',
                'bump2version',
                'coverage',
                'django-codemod',
                'django-debug-toolbar',
                'django-test-migrations',
                'django-upgrade',
                'flake8==3.5.0',
                'freezegun',
                'isort',
                'responses',
                'selenium',
                'Sphinx',
                'sphinx-rtd-theme',
                ],
    },

    project_urls={
        'Bug Reports': 'https://github.com/inyokaproject/inyoka/issues',
        'Source': 'https://github.com/inyokaproject/inyoka',
    },
)

