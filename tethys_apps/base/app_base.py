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
    Base class used for building apps
    """
    name = ''
    index = ''
    icon = ''
    root_url = ''
    color = ''

    def __repr__(self):
        """
        String representation
        """
        return '<TethysApp: {0}>'.format(self.name)

    def controllers(self, app):
        """
        Must return a list of AppController objects
        """
        raise NotImplementedError()
    
    def persistent_stores(self, controllers):
        """
        Should return a list of PersistentStore objects
        """
        pass