===========
Tethys Apps
===========

Tethys apps is an app that adds the capabilities to develop and host Tethys apps within your site.

Installation
------------

Tethys Gizmos can be installed via pip or by downloading the source. To install via pip or easy_install::

    pip install django-tethys_apps

To install via download::

    git clone https://github.com/swainn/django-tethys_apps.git
    cd django-tethys_gizmos
    python setup.py install

Django Configuration
--------------------

1. Add "tethys_apps" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = (
        ...
        'tethys_apps',
    )

2. Include the Tethys URLconf in your project urls.py like this::

    url(r'^apps/', include('tethys_apps.urls')),

3. Add the Tethys static files finder to STATICFILES_FINDERS setting. Also, include the default staticfiles finders::

    STATICFILES_FINDERS = ('django.contrib.staticfiles.finders.FileSystemFinder',
                           'django.contrib.staticfiles.finders.AppDirectoriesFinder',
                           'tethys_apps.utilities.TethysAppsStaticFinder')

4. Add the Tethys apps template loaders to the TEMPLATE_LOADERS setting. Also, include the default template loaders::

    TEMPLATE_LOADERS = ('django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader',
                        'tethys_apps.utilities.tethys_apps_template_loader')

5. Add the Tethys apps context processor and include all the default context processors::

    TEMPLATE_CONTEXT_PROCESSORS = ('django.contrib.auth.context_processors.auth',
                               'django.core.context_processors.debug',
                               'django.core.context_processors.i18n',
                               'django.core.context_processors.media',
                               'django.core.context_processors.static',
                               'django.core.context_processors.tz',
                               'django.contrib.messages.context_processors.messages',
                               'tethys_apps.context_processors.tethys_apps_context')

6. Tethys apps requires a PostgreSQL > 9.1 database with the PostGIS > 2.1 extension. Refer to the documentation for each
project for installation instructions. After installing the database, create two users with databases. Take note of the
passwords, you will need them in the next step::

	sudo -u postgres createuser -S -d -R -P tethys_db_manager
	sudo -u postgres createdb -O tethys_db_manager tethys_db_manager -E utf-8

	sudo -u postgres createuser --superuser -d -R -P tethys_super
	sudo -u postgres createdb -O tethys_super tethys_super -E utf-8

7. Provide the connection credentials for the two databases you created in SQLAlchemy syntax (Tethys apps use SQLAlchemy
--Not the Django ORM--for database communication). Replace "pass" with the passwords you gave the users::

    TETHYS_APPS_DATABASE_MANAGER_URL = 'postgresql://tethys_db_manager:pass@localhost:5432/tethys_db_manager'
    TETHYS_APPS_SUPERUSER = 'postgresql://tethys_super:pass@localhost:5432/tethys_super'

8. Run **python manage.py migrate** to create the database models.

9. Tethys Apps synthesizes several other django apps. They will be automatically installed when you run the setup script
but you will need to add the configuration parameters for those apps to your settings file. Rather than duplicate
the documentation for configuration of those apps here, please refer to the readme's for ecah of the following
django apps (which you can find on git hub):

* `django-tethys_gizmos <https://github.com/swainn/django-tethys_gizmos/blob/master/README.rst>`_

10. Start up the server with **python manage.py runserver** and visit http://127.0.0.1:8000/apps/ to view the apps library.