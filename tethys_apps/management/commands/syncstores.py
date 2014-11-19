from django.core.management.base import BaseCommand, make_option
from django.conf import settings

from tethys_apps.app_harvester import SingletonAppHarvester
from tethys_apps.terminal_colors import TerminalColors
from sqlalchemy import create_engine


class Command(BaseCommand):
    """
    Command class that handles the syncstores command. Provides persistent store management functionality.
    """
    option_list = BaseCommand.option_list + (
        make_option('-r', '--refresh',
                    action='store_true',
                    dest='refresh',
                    default=False,
                    help='When called with this option, the database will be dropped prior to syncing resulting in a '
                         'refreshed database.'),
    )

    def handle(self, *args, **options):
        """
        Handle the command
        """
        self.provision_persistent_stores(args, options)

    def provision_persistent_stores(self, app_names, options):
        """
        Provision all persistent stores for all apps or for only the app name given.
        """
        # Set refresh parameter
        database_refresh = options['refresh']

        # Get the app harvester
        app_harvester = SingletonAppHarvester()

        # Define the list of target apps
        target_apps = []
        target_apps_check = []

        for app in app_harvester.apps:
            # Derive app_name from the index which follows the pattern app_name:home
            if app.package in app_names:
                target_apps.append(app)
                target_apps_check.append(app.package)

        # Verify all apps included in target apps
        for app_name in app_names:
            if app_name not in target_apps_check:
                self.stdout.write('{0}WARNING:{1} The app named "{2}" cannot be found. Please make sure it is installed '
                                  'and try again.'.format(TerminalColors.WARNING, TerminalColors.ENDC, app_name))

        # Notify user of database provisioning
        self.stdout.write(TerminalColors.BLUE + '\nProvisioning Persistent Stores...' + TerminalColors.ENDC)

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
        connection.close()

        # Compile list of db names
        existing_db_names = []

        for existing_db in existing_dbs:
            existing_db_names.append(existing_db.name)

        # Get apps and provision persistent stores if not already created
        for app in target_apps:
            # Create multiple persistent stores if necessary
            persistent_stores = app.persistent_stores()

            if persistent_stores:
                for persistent_store in persistent_stores:
                    full_db_name = '_'.join((app.package, persistent_store.name))
                    new_database = True

                    #--------------------------------------------------------------------------------------------------#
                    # 1. Drop database if refresh option is included
                    #--------------------------------------------------------------------------------------------------#
                    if database_refresh and full_db_name in existing_db_names:
                        # Provide update for user
                        self.stdout.write('Dropping database {2}"{0}"{3} for app {2}"{1}"{3}...'.format(
                            persistent_store.name,
                            app.package,
                            TerminalColors.BLUE,
                            TerminalColors.ENDC
                        ))

                        # Connection
                        delete_connection = engine.connect()

                        # Drop db
                        drop_db_statement = 'DROP DATABASE IF EXISTS {0}'.format(full_db_name)

                        # Close transaction first then execute.
                        delete_connection.execute('commit')
                        delete_connection.execute(drop_db_statement)
                        delete_connection.close()

                        # Update the existing dbs query
                        existing_db_names.pop(existing_db_names.index(full_db_name))

                    #--------------------------------------------------------------------------------------------------#
                    # 2. Create the database if it does not already exist
                    #--------------------------------------------------------------------------------------------------#
                    if full_db_name not in existing_db_names:
                        # Provide Update for User
                        self.stdout.write('Creating database {2}"{0}"{3} for app {2}"{1}"{3}...'.format(
                            persistent_store.name,
                            app.package,
                            TerminalColors.BLUE,
                            TerminalColors.ENDC
                        ))

                        # Cannot create databases in a transaction: connect and commit to close transaction
                        create_connection = engine.connect()

                        # Create db
                        create_db_statement = '''
                                              CREATE DATABASE {0}
                                              WITH OWNER {1}
                                              TEMPLATE template0
                                              ENCODING 'UTF8'
                                              '''.format(full_db_name, database_manager_name)

                        # Close transaction first and then execute
                        create_connection.execute('commit')
                        create_connection.execute(create_db_statement)
                        create_connection.close()

                    else:
                        # Provide Update for User
                        self.stdout.write('Database {2}"{0}"{3} already exists for app {2}"{1}"{3}, skipping...'.format(
                            persistent_store.name,
                            app.package,
                            TerminalColors.BLUE,
                            TerminalColors.ENDC
                        ))

                        # Set var that is passed to initialization functions
                        new_database = False

                    #--------------------------------------------------------------------------------------------------#
                    # 3. Enable PostGIS extension
                    #--------------------------------------------------------------------------------------------------#
                    if (hasattr(persistent_store, 'spatial') and persistent_store.spatial) or persistent_store.postgis:
                        # Get URL for Tethys Superuser to enable extensions
                        super_url = settings.TETHYS_APPS_SUPERUSER_URL
                        super_parts = super_url.split('/')
                        new_db_url = '{0}//{1}/{2}'.format(super_parts[0], super_parts[2], full_db_name)

                        # Connect to new database
                        new_db_engine = create_engine(new_db_url)
                        new_db_connection = new_db_engine.connect()

                        # Notify user
                        self.stdout.write('Enabling PostGIS on database {2}"{0}"{3} for app {2}"{1}"{3}...'.format(
                            persistent_store.name,
                            app.package,
                            TerminalColors.BLUE,
                            TerminalColors.ENDC
                        ))
                        enable_postgis_statement = 'CREATE EXTENSION IF NOT EXISTS postgis'

                        # Execute postgis statement
                        new_db_connection.execute(enable_postgis_statement)
                        new_db_connection.close()

                #------------------------------------------------------------------------------------------------------#
                # 4. Run initialization functions for each store here
                #------------------------------------------------------------------------------------------------------#
                for persistent_store in persistent_stores:
                    # Split into module name and function name
                    initializer_mod, initializer_function = persistent_store.initializer.split(':')

                    self.stdout.write('Initializing database {3}"{0}"{4} for app {3}"{1}"{4} using initializer '
                                      '{3}"{2}"{4}...'.format(persistent_store.name,
                                                              app.package,
                                                              initializer_function,
                                                              TerminalColors.BLUE,
                                                              TerminalColors.ENDC
                                                              ))

                    # Pre-process initializer path
                    initializer_path = '.'.join(('tethys_apps.tethysapp', app.package, initializer_mod))

                    # Import module
                    module = __import__(initializer_path, fromlist=[initializer_function])

                    # Get the function
                    initializer = getattr(module, initializer_function)
                    initializer(new_database)

            # Spacer
            self.stdout.write('')