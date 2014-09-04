===========
Tethys Apps
===========

Tethys apps is an app that adds the capabilities to develop and host Tethys apps within your site.

Quick start
-----------

1. Add "tethys_apps" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = (
        ...
        'tethys_apps',
    )

2. Include the Tethys URLconf in your project urls.py like this::

    url(r'^apps/', include('tethys_apps.urls')),

3. Run `python manage.py migrate` to create the Tethys models.

4. Visit http://127.0.0.1:8000/apps/ to view the apps library.