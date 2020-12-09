"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    # https://packaging.python.org/specifications/core-metadata/#name
    name='Inyoka',
    # version defined via setup.cfg

    # https://packaging.python.org/specifications/core-metadata/#summary
    description='All-in-one portal software with Forum, Wiki, Planet, News and Calendar',

    # https://packaging.python.org/specifications/core-metadata/#description-optional
    long_description=long_description,
    long_description_content_type='text/markdown',

    # TODO: url='https://inyokaproject.org/' or 'https://github.com/inyokaproject/inyoka',

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
    keywords='Forum, Wiki, Planet, News, Calendar',

    packages=find_packages(),

    # Specify which Python versions you support
    # 'pip install' will check this
    # https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires
    python_requires='>=3.5, <4',

    install_requires=[
        'Django<2.0',
        'pip-tools',

        'Babel==2.8.0',
        'beautifulsoup4==4.6.0',
        'celery==4.3.0',
        'certifi',
        'defusedxml==0.6.0',
        'django-filter==1.0.4',
        'django-guardian==1.4.9',
        'django-hosts==3.0',
        'django-redis==4.11.0',
        'dnspython==1.16.0',
        'feedparser==6.0.0b3',
        'gunicorn==20.0.4',
        'html5lib==1.1',
        'icalendar==4.0.7',
        'Jinja2==2.11.2',
        'lxml<4.7',
        'Pillow<8',
        'psycopg2',
        'Pygments',
        'python-magic==0.4.18',
        'python-dateutil',
        'pytz',
        'pyzmq==16.0.4',
        'raven==6.3.0',
        'requests',
        'slixmpp==1.4.2',
        'transifex-client==0.12.5',
        'Werkzeug==0.15.5'
    ],

    # TODO: pip-tools currently does not support groups → reason why extra/requirements/development.in exists
    # Additional groups of dependencies here (e.g. development
    # dependencies). Users will be able to install these using the "extras"
    # syntax, for example:
    #
    #   $ pip install sampleproject[dev]
    #extras_require={  # Optional
    #    'dev': ['check-manifest'],
    #},

    # https://packaging.python.org/specifications/core-metadata/#project-url-multiple-use
    project_urls={
        'Bug Reports': 'https://github.com/inyokaproject/inyoka/issues',
        'Source': 'https://github.com/inyokaproject/inyoka',
    },
)

