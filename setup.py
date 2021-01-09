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
    python_requires='>=3.5, <4',
    install_requires=[
        'Django<2.3',
        'pip-tools',

        'Babel',
        'beautifulsoup4==4.6.0',
        'celery[redis]==4.3.0',
        'certifi',
        'defusedxml==0.6.0',
        'django-filter<3',
        'django-guardian<2.4',
        'django-hosts',
        'django-redis',
        'dnspython==1.16.0',
        'feedparser==6.0.0b3',
        'gunicorn',
        'html5lib==1.1',
        'icalendar',
        'Jinja2<3',
        'lxml<4.7',
        'Pillow<8',
        'psycopg2',
        'Pygments',
        'python-magic',
        'python-dateutil',
        'pytz',
        'pyzmq',
        'raven',
        'requests',
        'slixmpp==1.4.2',
        'transifex-client==0.12.5',
        'Werkzeug==0.15.5'
    ],

    project_urls={
        'Bug Reports': 'https://github.com/inyokaproject/inyoka/issues',
        'Source': 'https://github.com/inyokaproject/inyoka',
    },
)

