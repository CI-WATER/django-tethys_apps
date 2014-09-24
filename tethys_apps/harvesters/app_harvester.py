"""
********************************************************************************
* Name: app_harvester
* Author: Nathan Swain and Scott Christensen
* Created On: August 19, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
"""

import os
import inspect

from django.conf import settings
from sqlalchemy import create_engine

from tethys_apps.base import TethysAppBase


class SingletonAppHarvester(object):
    """
    Collects information for initiating apps
    """

    apps = []
    _instance = None

    def harvest_apps(self):
        """
        Searches the apps package for apps
        """
        # Notify user harvesting is taking place
        print('Harvesting Apps:')

        # List the apps packages in directory
        apps_dir = os.path.join(os.path.split(os.path.dirname(__file__))[0], 'tethysapp')
        app_packages_list = os.listdir(apps_dir)

        # Harvest App Instances
        self._harvest_app_instances(app_packages_list)

        # Create Persistent stores
        self._provision_persistent_stores()
        #self._run_initialization_scripts()
        
    def __new__(self):
        """
        Make App Harvester a Singleton
        """
        if not self._instance:
            self._instance = super(SingletonAppHarvester, self).__new__(self)
            
        return self._instance

    @staticmethod
    def _validate_app(app):
        """
        Validate the app data that needs to be validated. Returns either the app if valid or None if not valid.
        """
        # Remove prepended slash if included
        if app.icon != '' and app.icon[0] == '/':
            app.icon = app.icon[1:]

        # Validate color
        if app.color != '' and app.color[0] != '#':
            # Add hash
            app.color = '#{0}'.format(app.color)

        # Must be 6 or 3 digit hex color (7 or 4 with hash symbol)
        if len(app.color) != 7 and len(app.color) != 4:
            app.color = ''

        return app

    def _harvest_app_instances(self, app_packages_list):
        """
        Search each app package for the app.py module. Find the AppBase class in the app.py
        module and instantiate it. Save the list of instantiated AppBase classes.
        """
        valid_app_instance_list = []
        
        for app_package in app_packages_list:
            # Collect data from each app package in the apps directory
            if app_package not in ['__init__.py', '__init__.pyc', '.gitignore', '.DS_Store']:
                # Create the path to the app module in the custom app package
                app_module_name = '.'.join(['tethys_apps.tethysapp', app_package, 'app'])

                # Import the app.py module from the custom app package programmatically
                # (e.g.: apps.apps.<custom_package>.app)
                app_module = __import__(app_module_name, fromlist=[''])
                
                for name, obj in inspect.getmembers(app_module):
                    # Retrieve the members of the app_module and iterate through
                    # them to find the the class that inherits from AppBase.
                    try:
                        # issubclass() will fail if obj is not a class
                        if (issubclass(obj, TethysAppBase)) and (obj is not TethysAppBase):
                            # Assign a handle to the class
                            _appClass = getattr(app_module, name)

                            # Instantiate app and validate
                            app_instance = _appClass()
                            validated_app_instance = self._validate_app(app_instance)

                            # compile valid apps
                            if validated_app_instance:
                                valid_app_instance_list.append(validated_app_instance)

                                # Notify user that the app has been loaded
                                print('{0}'.format(app_package))

                    except TypeError:
                        '''DO NOTHING'''
                    except:
                        raise

        # Save valid apps
        self.apps = valid_app_instance_list

    def _provision_persistent_stores(self):
        """
        Provision all persistent stores in the requested_stores property
        """
        # Notify user of database provisioning
        print('\nProvisioning Persistent Stores:')

        # Get database manager url from the config
        database_manager_url = settings.TETHYS_APPS_DATABASE_MANAGER_URL
        database_manager_name = database_manager_url.split('://')[1].split(':')[0]

        #--------------------------------------------------------------------------------------------------------------#
        # Get a list of existing databases
        #--------------------------------------------------------------------------------------------------------------#

        # Create connection engine
        engine = create_engine(database_manager_url)

        # Cannot create databases in a transaction: connect and commit to close transaction
        connection = engine.connect()

        # Check for Database
        existing_dbs_statement = '''
                                 SELECT d.datname as name
                                 FROM pg_catalog.pg_database d
                                 LEFT JOIN pg_catalog.pg_user u ON d.datdba = u.usesysid
                                 ORDER BY 1;
                                 '''

        existing_dbs = connection.execute(existing_dbs_statement)

        # Compile list of db names
        existing_db_names = []

        for existing_db in existing_dbs:
            existing_db_names.append(existing_db.name)

        # Get apps and provision persistent stores if not already created
        for app in self.apps:
            # Create multiple persistent stores if necessary
            for persistent_store in app.persistent_stores():
                full_db_name = '_'.join((app.package, persistent_store.name))
                new_database = True

                #------------------------------------------------------------------------------------------------------#
                # 1. Create the database if it does not already exist
                #------------------------------------------------------------------------------------------------------#
                if full_db_name not in existing_db_names:
                    # Provide Update for User
                    print('Creating database "{0}" for app "{1}"...'.format(persistent_store.name, app.package))

                    # Create db
                    create_db_statement = '''
                                          CREATE DATABASE {0}
                                          WITH OWNER {1}
                                          TEMPLATE template0
                                          ENCODING 'UTF8'
                                          '''.format(full_db_name, database_manager_name)

                    # Close transaction first and then execute
                    connection.execute('commit')
                    connection.execute(create_db_statement)

                else:
                    # Provide Update for User
                    print('Database "{0}" already exists for app "{1}", skipping...'.format(persistent_store.name,
                                                                                            app.package))

                    # Set var that is passed to initialization functions
                    new_database = False

                #------------------------------------------------------------------------------------------------------#
                # 2. Enable PostGIS extension
                #------------------------------------------------------------------------------------------------------#
                if persistent_store.postgis:
                    # Get URL for Tethys Superuser to enable extensions
                    super_url = settings.TETHYS_APPS_SUPERUSER
                    super_parts = super_url.split('/')
                    new_db_url = '{0}//{1}/{2}'.format(super_parts[0], super_parts[2], full_db_name)

                    # Connect to new database
                    new_db_engine = create_engine(new_db_url)
                    new_db_connection = new_db_engine.connect()

                    # Notify user
                    print('Enabling PostGIS on database "{0}" for app "{1}"...'.format(persistent_store.name,
                                                                                       app.package))
                    enable_postgis_statement = 'CREATE EXTENSION IF NOT EXISTS postgis'

                    # Execute postgis statement
                    new_db_connection.execute(enable_postgis_statement)
                    connection.close()
                #------------------------------------------------------------------------------------------------------#
                # 3. Run initialization function here
                #------------------------------------------------------------------------------------------------------#
                print('Initialize database "{0}" for app "{1}"'.format(persistent_store.name, app.package))

                # Split into module name and function name
                initializer_mod, initializer_function = persistent_store.initializer.split(':')

                # Pre-process initializer path
                initializer_path = '.'.join(('tethys_apps.tethysapp', app.package, initializer_mod))

                # Import module
                module = __import__(initializer_path, fromlist=[initializer_function])

                # Get the function
                initializer = getattr(module, initializer_function)
                initializer(new_database)

                #Spacer
                print('')
