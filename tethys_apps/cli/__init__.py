# Commandline interface for Tethys
import argparse
import subprocess

GEN_SETTINGS_OPTION = 'settings'
VALID_GEN_OBJECTS = (GEN_SETTINGS_OPTION,)


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
    print(args.type)


def start_dev_server_command(args):
    """
    Start up the development server.
    """
    print 'start'


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
    gen_parser.set_defaults(func=generate_command)

    # Setup start server parsers
    start_parser = subparsers.add_parser('start', help='Shortcut for starting Tethys development server.')
    start_parser.set_defaults(func=start_dev_server_command)

    # Parse the args and call the default function
    args = parser.parse_args()
    args.func(args)