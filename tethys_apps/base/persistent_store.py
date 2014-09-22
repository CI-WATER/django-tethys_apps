"""
********************************************************************************
* Name: persistent store
* Author: Nathan Swain
* Created On: September 22, 2014
* Copyright: (c) Brigham Young University 2014
* License: BSD 2-Clause
********************************************************************************
"""


class PersistentStore(object):
    """
    An object that stores the data for a Tethys Persistent store
    """

    def __init__(self, name, initializer, postgis=False):
        """
        Constructor
        """
        self.name = name
        self.initializer = initializer
        self.postgis = postgis

    def __repr__(self):
        """
        String representation
        """
        return '<Persistent Store: name={0}, initializer={1}, postgis={2}>'.format(self.name,
                                                                                   self.initializer,
                                                                                   self.postgis)