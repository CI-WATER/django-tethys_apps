import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

requires = ['django',
            'PasteScript>=1.3',
            'sqlalchemy',
            'psycopg2',
            'django-tethys_gizmos']

version = '0.1.2'

setup(
    name='django-tethys_apps',
    version=version,
    packages=['tethys_apps'],
    include_package_data=True,
    license='BSD 2-Clause License',
    description='An app to enable development and hosting capabilities for Tethys Apps.',
    long_description=README,
    url='',
    author='Nathan Swain',
    author_email='nathan.swain@byu.net',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License', # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    entry_points = {
        'console_scripts': ['tethys=tethys_apps.cli:tethys_command',],
        'paste.paster_create_template': ['tethys_app_scaffold=tethys_apps.pastetemplates:TethysAppTemplate',],
    },
    install_requires = requires,
)