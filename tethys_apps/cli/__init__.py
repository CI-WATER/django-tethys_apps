# Commandline interface for Tethys
import argparse
import subprocess
import os
import random
import string

from django.template import Template, Context
from django.conf import settings

# Module level variables
GEN_SETTINGS_OPTION = 'settings'
VALID_GEN_OBJECTS = (GEN_SETTINGS_OPTION,)
DEFAULT_INSTALLATION_DIRECTORY = '/usr/lib/tethys/src'
DEVELOPMENT_DIRECTORY = '/usr/lib/tethys/tethys'

# Setup Django settings
settings.configure()


def scaffold_command(args):
    """
    Create a new Tethys app projects in the current directory.
    """
    PREFIX = 'tethysapp'
    project_name = args.name

    if PREFIX not in project_name:
        project_name = '{0}-{1}'.format(PREFIX, project_name)

    process = ['paster', 'create', '-t', 'tethys_app_scaffold', project_name]
    subprocess.call(process)


def generate_command(args):
    """
    Generate a settings file for a new installation.
    """
    # Setup variables
    template = None
    context = Context()

    # Determine template path
    gen_templates_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'gen_templates')
    template_path = os.path.join(gen_templates_dir, args.type)

    # Determine destination file name (defaults to type)
    destination_file = args.type

    # Settings file setup
    if args.type == GEN_SETTINGS_OPTION:
        # Desitnation filename
        destination_file = '{0}.py'.format(args.type)

        # Parse template
        template = Template(open(template_path).read())

        # Generate context variables
        secret_key = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(50)])
        context.update({'secret_key': secret_key})
        print('Generating new settings.py file...')

    # Default destination path is the current working directory
    destination_dir = os.getcwd()

    if args.directory:
        if os.path.isdir(args.directory):
            destination_dir = args.directory
        else:
            print('Error: "{0}" is not a valid directory.')
            exit(1)

    destination_path = os.path.join(destination_dir, destination_file)

    # Check for pre-existing file
    if os.path.isfile(destination_path):
        valid_inputs = ('y', 'n', 'yes', 'no')
        no_inputs = ('n', 'no')

        overwrite_input = raw_input('Warning: "{0}" already exists. '
                                    'Overwrite? (y/n): '.format(destination_file)).lower()

        while overwrite_input not in valid_inputs:
            overwrite_input = raw_input('Invalid option. Overwrite? (y/n): ').lower()

        if overwrite_input in no_inputs:
            print('Generation of "{0}" cancelled.'.format(destination_file))
            exit(0)

    # Render template and write to file
    if template:
        with open(destination_path, 'w') as f:
            f.write(template.render(context))


def manage_command(args):
    """
    Start up the development server.
    """
    # Determine path to manage.py file
    manage_path = os.path.join(DEFAULT_INSTALLATION_DIRECTORY, 'manage.py')

    # Check for path option
    if args.manage:
        manage_path = args.manage

        # Throw error if path is not valid
        if not os.path.isfile(manage_path):
            print('Error: Can\'t open file "{0}", no such file.'.format(manage_path))
            exit(1)

    elif not os.path.isfile(manage_path):
        # Try the development path version
        manage_path = os.path.join(DEVELOPMENT_DIRECTORY, 'manage.py')

        # Throw error if default path is not valid
        if not os.path.isfile(manage_path):
            print('Error: Cannot find the "manage.py" file at the default location. Try using the "--manage"'
                  'option to provide the path to the location of the "manage.py" file.')
            exit(1)

    # Run the command
    if args.command == 'start':
        if args.port:
            process = ['python', manage_path, 'runserver', str(args.port)]
        else:
            process = ['python', manage_path, 'runserver']
    elif args.command == 'syncdb':
        process = ['python', manage_path, 'syncdb']
    else:
        process = None

    # Call the process with a little trick to ignore the keyboard interrupt error when it happens
    if process:
        try:
            subprocess.call(process)
        except KeyboardInterrupt:
            pass


def tethys_command():
    """
    Tethys commandline interface function.
    """
    # Create parsers
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='Commands')

    # Setup scaffold parsers
    scaffold_parser = subparsers.add_parser('scaffold', help='Create a new Tethys app project from a scaffold.')
    scaffold_parser.add_argument('name', help='The name of the new Tethys app project to create.')
    scaffold_parser.set_defaults(func=scaffold_command)

    # Setup generate command
    gen_parser = subparsers.add_parser('gen', help='Create aids the setup of Tethys by automating '
                                                   'creation of supporting files.')
    gen_parser.add_argument('type', help='The type of object to generate.', choices=VALID_GEN_OBJECTS)
    gen_parser.add_argument('-d', '--directory', help='Destination directory for the generated object.')
    gen_parser.set_defaults(func=generate_command)

    # Setup start server parsers
    manage_parser = subparsers.add_parser('manage', help='Management commands for Tethys Platform.')
    manage_parser.add_argument('command', help='Management command to run.', choices=['start', 'syncdb'])
    manage_parser.add_argument('-m', '--manage', help='Absolute path to manage.py for Tethys Platform installation.')
    manage_parser.add_argument('-p', '--port', type=int, help='Port on which to start the development server.')
    manage_parser.set_defaults(func=manage_command)

    # Parse the args and call the default function
    args = parser.parse_args()
    args.func(args)