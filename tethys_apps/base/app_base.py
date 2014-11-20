"""
********************************************************************************
* Name: app_base.py
* Author: Nathan Swain and Scott Christensen
* Created On: August 19, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""


class TethysAppBase(object):
    """
    Base class used to define the app class for Tethys apps.

    Attributes:
      name(string): Name of the app.
      index(string): Lookup term for the index URL of the app.
      icon(string): Location of the image to use for the app icon.
      package(string): Name of the app package.
      root_url(string): Root URL of the app.
      color(string): App theme color as RGB hexadecimal.
    """
    name = ''
    index = ''
    icon = ''
    package = ''
    root_url = ''
    color = ''

    def __repr__(self):
        """
        String representation
        """
        return '<TethysApp: {0}>'.format(self.name)

    def url_map(self):
        """
        Use this method to define the URL Maps for your app.

        Returns:
          iterable: A list or tuple of UrlMap objects.
        """
        raise NotImplementedError()
    
    def persistent_stores(self):
        """
        Define this method to register persistent store databases for your app. You may define up to 5 persistent stores for an app.

        Returns:
          iterable: A list or tuple of PersistentStore objects. A persistent store database will be created for each object.
        """
        return None

    def dataset_services(self):
        """
        Use this method to define dataset service connections for use in your app.

        Returns:
          iterable: A list or tuple of DatasetService objects.
        """
        return None