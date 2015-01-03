import subprocess
from subprocess import Popen, PIPE
import os
import sys
import time
import json
import getpass
from exceptions import OSError
from functools import cmp_to_key
from docker.utils import kwargs_from_env, compare_version
from docker.client import Client as DockerClient, DEFAULT_DOCKER_API_VERSION as MAX_CLIENT_DOCKER_API_VERSION

__all__ = ['docker_init', 'docker_start',
           'docker_stop', 'docker_status',
           'docker_update', 'docker_remove',
           'docker_ip']

MINIMUM_API_VERSION = '1.12'

OSX = 1
WINDOWS = 2
LINUX = 3

POSTGIS_IMAGE = 'ciwater/postgis:latest'
GEOSERVER_IMAGE = 'ciwater/geoserver:latest'
N52WPS_IMAGE = 'ciwater/n52wps:latest'

REQUIRED_DOCKER_IMAGES = [POSTGIS_IMAGE,
                          GEOSERVER_IMAGE,
                          N52WPS_IMAGE]

POSTGIS_CONTAINER = 'tethys_postgis'
GEOSERVER_CONTAINER = 'tethys_geoserver'
N52WPS_CONTAINER = 'tethys_wps'

REQUIRED_DOCKER_CONTAINERS = [POSTGIS_CONTAINER,
                              GEOSERVER_CONTAINER,
                              N52WPS_CONTAINER]


def get_api_version(*versions):
    """
    Find the right version of the client to use.
    credits: @kevinastone https://github.com/docker/docker-py/issues/439
    """
    # compare_version is backwards
    def cmp(a, b):
        return -1 * compare_version(a, b)
    return min(versions, key=cmp_to_key(cmp))


def get_docker_client():
    """
    Try to fire up boot2docker and set any environmental variables
    """
    # For Mac
    try:
        # Get boot2docker info (will fail if not Mac)
        process = ['boot2docker', 'info']
        p = subprocess.Popen(process, stdout=PIPE)
        boot2docker_info = json.loads(p.communicate()[0])

        # for k, v in boot2docker_info.iteritems():
        #     print k, v

        # Start the boot2docker VM if it is not already running
        if boot2docker_info['State'] != "running":
            print('Starting Boot2Docker VM:')
            # Start up the Docker VM
            process = ['boot2docker', 'start']
            subprocess.call(process)

        if ('DOCKER_HOST' not in os.environ) or ('DOCKER_CERT_PATH' not in os.environ) or ('DOCKER_TLS_VERIFY' not in os.environ):
            # Get environmental variable values
            process = ['boot2docker', 'shellinit']
            p = subprocess.Popen(process, stdout=PIPE)
            boot2docker_envs = p.communicate()[0].split()

            docker_host = ''
            docker_cert_path = ''
            docker_tls_verify = ''

            for env in boot2docker_envs:
                if 'DOCKER_HOST' in env:
                    docker_host = env.split('=')[1]
                elif 'DOCKER_CERT_PATH' in env:
                    docker_cert_path = env.split('=')[1]
                elif 'DOCKER_TLS_VERIFY' in env:
                    docker_tls_verify = env.split('=')[1]

            # Set environmental variables
            os.environ['DOCKER_TLS_VERIFY'] = docker_tls_verify
            os.environ['DOCKER_HOST'] = docker_host
            os.environ['DOCKER_CERT_PATH'] = docker_cert_path

        # Get the arguments form the environment
        client_kwargs = kwargs_from_env(assert_hostname=False)
        client_kwargs['version'] = MINIMUM_API_VERSION

        # Find the right version of the API by creating a DockerClient with the minimum working version
        # Then test to see if the Docker is running a later version than the minimum
        # See: https://github.com/docker/docker-py/issues/439
        version_client = DockerClient(**client_kwargs)
        client_kwargs['version'] = get_api_version(MAX_CLIENT_DOCKER_API_VERSION, version_client.version()['ApiVersion'])

        # Create Real Docker client
        return DockerClient(**client_kwargs)

    # For Linux
    except OSError:
        # Find the right version of the API by creating a DockerClient with the minimum working version
        # Then test to see if the Docker is running a later version than the minimum
        # See: https://github.com/docker/docker-py/issues/439
        version_client = DockerClient(base_url='unix://var/run/docker.sock', version=MINIMUM_API_VERSION)
        version = get_api_version(MAX_CLIENT_DOCKER_API_VERSION, version_client.version()['ApiVersion'])
        return DockerClient(base_url='unix://var/run/docker.sock', version=version)

    except:
        raise


def get_images_to_install(docker_client):
    """
    Get a list of the Docker images that are not already installed/pulled.

    Args:
      docker_client(docker.client.Client): docker-py client.

    Returns:
      (list): A list of the image tags that need to be installed.
    """
    # All assumed to need installing by default
    images_to_install = REQUIRED_DOCKER_IMAGES

    # List the images
    images = docker_client.images()

    # Search through all the images already installed (pulled)
    for image in images:
        tags = image['RepoTags']

        # If one of the required docker images is listed, remove it from the list of images to be installed
        for required_docker_image in REQUIRED_DOCKER_IMAGES:
            if required_docker_image in tags:
                images_to_install.pop(images_to_install.index(required_docker_image))

    return images_to_install


def get_containers_to_create(docker_client):
    """
    Get a list of containers that need to be created.
    """
    # All assumed to need creating by default
    containers_to_create = REQUIRED_DOCKER_CONTAINERS

    # Create containers for each image if not done already
    containers = docker_client.containers(all=True)

    for container in containers:
        names = container['Names']

        # If one of the required containers is listed, remove it from the list of containers to create
        for required_docker_container in REQUIRED_DOCKER_CONTAINERS:
            if '/' + required_docker_container in names:
                containers_to_create.pop(containers_to_create.index(required_docker_container))

    return containers_to_create


def log_pull_stream(stream):
    """
    Handle the printing of pull statuses
    """
    # Experimental printing
    previous_id = ''
    previous_message = ''

    for line in stream:
        json_line = json.loads(line)
        current_id = json_line['id'] if 'id' in json_line else ''
        current_status = json_line['status'] if 'status' in json_line else ''

        # Update prompt
        backspaces = '\b' * len(previous_message)
        spaces = ' ' * len(previous_message)
        current_message = '\n{0}: {1}'.format(current_id, current_status)

        if current_status == 'Downloading' or current_status == 'Extracting':
            current_message = '{0} {1}'.format(current_message, json_line['progress'])

        # Handle no id case
        if not current_id:
            sys.stdout.write('\n{0}'.format(current_status))

        # Overwrite current line if id is the same
        elif current_id == previous_id:
            sys.stdout.write(backspaces)
            sys.stdout.write(spaces)
            sys.stdout.write(backspaces)
            sys.stdout.write(current_message.strip())

        # Start new line
        else:
            sys.stdout.write(current_message)

        # Flush to out
        sys.stdout.flush()

        # Save state
        previous_message = current_message
        previous_id = current_id
    print()


def get_docker_container_dicts(docker_client):
    # Check status of containers
    containers = docker_client.containers(all=True)
    container_dicts = dict()

    for container in containers:

        if '/' + POSTGIS_CONTAINER in container['Names']:
            container_dicts[POSTGIS_CONTAINER] = container

        elif '/' + GEOSERVER_CONTAINER in container['Names']:
            container_dicts[GEOSERVER_CONTAINER] = container

        elif '/' + N52WPS_CONTAINER in container['Names']:
            container_dicts[N52WPS_CONTAINER] = container

    return container_dicts


def get_docker_container_status(docker_client):
    # Check status of containers
    containers = docker_client.containers()
    container_status = {POSTGIS_CONTAINER: False,
                        GEOSERVER_CONTAINER: False,
                        N52WPS_CONTAINER: False}

    for container in containers:

        if '/' + POSTGIS_CONTAINER in container['Names']:
            container_status[POSTGIS_CONTAINER] = True

        elif '/' + GEOSERVER_CONTAINER in container['Names']:
            container_status[GEOSERVER_CONTAINER] = True

        elif '/' + N52WPS_CONTAINER in container['Names']:
            container_status[N52WPS_CONTAINER] = True

    return container_status


def install_docker_containers(docker_client, force=False, container=None, defaults=False):
    """
    Install all Docker containers
    """
    # Check for containers that need to be created
    containers_to_create = get_containers_to_create(docker_client)

    # PostGIS
    if POSTGIS_CONTAINER in containers_to_create or force:
        print("Installing the PostGIS Docker container...")

        # Default environmental vars
        tethys_default_pass = 'pass'
        tethys_db_manager_pass = 'pass'
        tethys_super_pass = 'pass'

        # User environmental variables
        if not defaults:
            print("Provide passwords for the three Tethys database users or press enter to accept the default "
                  "passwords shown in square brackets:")

            # tethys_default
            tethys_default_pass_1 = getpass.getpass('Password for "tethys_default" database user [pass]: ')

            if tethys_default_pass_1 != '':
                tethys_default_pass_2 = getpass.getpass('Confirm password for "tethys_default" database user: ')

                while tethys_default_pass_1 != tethys_default_pass_2:
                    print('Passwords do not match, please try again: ')
                    tethys_default_pass_1 = getpass.getpass('Password for "tethys_default" database user [pass]: ')
                    tethys_default_pass_2 = getpass.getpass('Confirm password for "tethys_default" database user: ')

                tethys_default_pass = tethys_default_pass_1
            else:
                tethys_default_pass = 'pass'

            # tethys_db_manager
            tethys_db_manager_pass_1 = getpass.getpass('Password for "tethys_db_manager" database user [pass]: ')

            if tethys_db_manager_pass_1 != '':
                tethys_db_manager_pass_2 = getpass.getpass('Confirm password for "tethys_db_manager" database user: ')

                while tethys_db_manager_pass_1 != tethys_db_manager_pass_2:
                    print('Passwords do not match, please try again: ')
                    tethys_db_manager_pass_1 = getpass.getpass('Password for "tethys_db_manager" database user [pass]: ')
                    tethys_db_manager_pass_2 = getpass.getpass('Confirm password for "tethys_db_manager" database user: ')

                tethys_db_manager_pass = tethys_db_manager_pass_1
            else:
                tethys_db_manager_pass = 'pass'

            # tethys_super
            tethys_super_pass_1 = getpass.getpass('Password for "tethys_super" database user [pass]: ')

            if tethys_super_pass_1 != '':
                tethys_super_pass_2 = getpass.getpass('Confirm password for "tethys_super" database user: ')

                while tethys_super_pass_1 != tethys_super_pass_2:
                    print('Passwords do not match, please try again: ')
                    tethys_super_pass_1 = getpass.getpass('Password for "tethys_super" database user [pass]: ')
                    tethys_super_pass_2 = getpass.getpass('Confirm password for "tethys_super" database user: ')

                tethys_super_pass = tethys_super_pass_1
            else:
                tethys_super_pass = 'pass'

        postgis_container = docker_client.create_container(name=POSTGIS_CONTAINER,
                                                           image=POSTGIS_IMAGE,
                                                           environment={'TETHYS_DEFAULT_PASS': tethys_default_pass,
                                                                        'TETHYS_DB_MANAGER_PASS': tethys_db_manager_pass,
                                                                        'TETHYS_SUPER_PASS': tethys_super_pass}
        )

    else:
        print("PostGIS Docker container already installed: skipping.")

    # GeoServer
    if GEOSERVER_CONTAINER in containers_to_create or force:
        print("Installing the GeoServer Docker container...")

        geoserver_container = docker_client.create_container(name=GEOSERVER_CONTAINER,
                                                             image=GEOSERVER_IMAGE
        )

    else:
        print("GeoServer Docker container already installed: skipping.")

    # 52 North WPS
    if N52WPS_CONTAINER in containers_to_create or force:
        print("Installing the 52 North WPS Docker container...")

        # Default environmental vars
        name = 'NONE'
        position = 'NONE'
        address = 'NONE'
        city = 'NONE'
        state = 'NONE'
        country = 'NONE'
        postal_code = 'NONE'
        email = 'NONE'
        phone = 'NONE'
        fax = 'NONE'
        username = 'wps'
        password = 'wps'

        if not defaults:
            print("Provide contact information for the 52 North Web Processing Service or press enter to accept the "
                  "defaults shown in square brackets: ")

            name = raw_input('Name [NONE]: ')
            if name == '':
                name = 'NONE'

            position = raw_input('Position [NONE]: ')
            if position == '':
                position = 'NONE'

            address = raw_input('Address [NONE]: ')
            if address == '':
                address = 'NONE'

            city = raw_input('City [NONE]: ')
            if city == '':
                city = 'NONE'

            state = raw_input('State [NONE]: ')
            if state == '':
                state = 'NONE'

            country = raw_input('Country [NONE]: ')
            if country == '':
                country = 'NONE'

            postal_code = raw_input('Postal Code [NONE]: ')
            if postal_code == '':
                postal_code = 'NONE'

            email = raw_input('Email [NONE]: ')
            if email == '':
                email = 'NONE'

            phone = raw_input('Phone [NONE]: ')
            if phone == '':
                phone = 'NONE'

            fax = raw_input('Fax [NONE]: ')
            if fax == '':
                fax = 'NONE'

            username = raw_input('Admin Username [wps]: ')

            if username == '':
                username = 'wps'

            password_1 = getpass.getpass('Admin Password [wps]: ')

            if password_1 == '':
                password = 'wps'

            else:
                password_2 = getpass.getpass('Confirm Password: ')

                while password_1 != password_2:
                    print('Passwords do not match, please try again.')
                    password_1 = getpass.getpass('Admin Password [wps]: ')
                    password_2 = getpass.getpass('Confirm Password: ')

                password = password_1




        wps_container = docker_client.create_container(name=N52WPS_CONTAINER,
                                                       image=N52WPS_IMAGE,
                                                       environment={'NAME': name,
                                                                    'POSITION': position,
                                                                    'ADDRESS': address,
                                                                    'CITY': city,
                                                                    'STATE': state,
                                                                    'COUNTRY': country,
                                                                    'POSTAL_CODE': postal_code,
                                                                    'EMAIL': email,
                                                                    'PHONE': phone,
                                                                    'FAX': fax,
                                                                    'USERNAME': username,
                                                                    'PASSWORD': password}
        )

    else:
        print("52 North WPS Docker container already installed: skipping.")

    print("The Docker containers have been successfully installed.")


def container_check(docker_client):
    """
    Check to ensure containers are installed.
    """
    # Perform this check to make sure the "tethys docker init" command has been run
    containers_needing_to_be_installed = get_containers_to_create(docker_client)

    if len(containers_needing_to_be_installed) > 0:
        print('The following Docker containers have not been installed: {0}'.format(
            ', '.join(containers_needing_to_be_installed)))
        print('Run the "tethys docker init" command to install them.')
        exit(1)


def start_docker_containers(docker_client):
    """
    Start all Docker containers
    """
    # Perform check
    container_check(docker_client)

    # Get container dicts
    container_status = get_docker_container_status(docker_client)

    # Start PostGIS
    if not container_status[POSTGIS_CONTAINER]:
        print('Starting PostGIS container...')
        docker_client.start(container=POSTGIS_CONTAINER,
                            port_bindings={5432: 5432})
    else:
        print('PostGIS container already running...')

    if not container_status[GEOSERVER_CONTAINER]:
        # Start GeoServer
        print('Starting GeoServer container...')
        docker_client.start(container=GEOSERVER_CONTAINER,
                            port_bindings={8080: 8080})
    else:
        print('GeoServer container already running...')

    if not container_status[N52WPS_CONTAINER]:
        # Start 52 North WPS
        print('Starting 52 North WPS container...')
        docker_client.start(container=N52WPS_CONTAINER,
                            port_bindings={8080: 8888})
    else:
        print('52 North WPS container already running...')


def stop_docker_containers(docker_client, silent=False):
    """
    Stop all Docker containers
    """
    # Perform check
    container_check(docker_client)

    # Get container dicts
    container_status = get_docker_container_status(docker_client)

    # Stop PostGIS
    if container_status[POSTGIS_CONTAINER]:
        if not silent:
            print('Stopping PostGIS container...')

        docker_client.stop(container=POSTGIS_CONTAINER)

    elif not silent:
        print('PostGIS container already stopped.')

    # Stop GeoServer
    if container_status[GEOSERVER_CONTAINER]:
        if not silent:
            print('Stopping GeoServer container...')

        docker_client.stop(container=GEOSERVER_CONTAINER)

    elif not silent:
        print('GeoServer container already stopped.')

    # Stop 52 North WPS
    if container_status[N52WPS_CONTAINER]:
        if not silent:
            print('Stopping 52 North WPS container...')

        docker_client.stop(container=N52WPS_CONTAINER)

    elif not silent:
        print('52 North WPS container already stopped.')


def remove_docker_containers(docker_client):
    """
    Remove all docker containers
    """
    # Perform check
    container_check(docker_client)

    # Remove PostGIS
    print('Removing PostGIS...')
    docker_client.remove_container(container=POSTGIS_CONTAINER)

    # Remove GeoServer
    print('Removing GeoServer...')
    docker_client.remove_container(container=GEOSERVER_CONTAINER)

    # Remove 52 North WPS
    print('Removing 52 North WPS...')
    docker_client.remove_container(container=N52WPS_CONTAINER)


def docker_init(container=None, defaults=False):
    """
    Pull Docker images for Tethys Platform and create containers with interactive input.
    """
    # Retrieve a Docker client
    docker_client = get_docker_client()

    # Check for the correct images
    images_to_install = get_images_to_install(docker_client)

    if len(images_to_install) < 1:
        print("Docker images already pulled.")
    else:
        print("Pulling Docker images...")

    # Pull the Docker images
    for image in images_to_install:
        pull_stream = docker_client.pull(image, stream=True)
        log_pull_stream(pull_stream)

    # Install docker containers
    install_docker_containers(docker_client, container, defaults)


def docker_start(container=None, defaults=False):
    """
    Start the docker containers
    """
    # Retrieve a Docker client
    docker_client = get_docker_client()

    # Start the Docker containers
    start_docker_containers(docker_client)


def docker_stop(container=None, defaults=False):
    """
    Stop Docker containers
    """
    # Retrieve a Docker client
    docker_client = get_docker_client()

    # Stop the Docker containers
    stop_docker_containers(docker_client)


def docker_remove(container=None, defaults=False):
    """
    Remove Docker containers.
    """
    # Retrieve a Docker client
    docker_client = get_docker_client()

    # Stop the Docker containers
    stop_docker_containers(docker_client)

    # Remove Docker containers
    remove_docker_containers(docker_client)


def docker_status(container=None, defaults=False):
    """
    Returns the status of the Docker containers: either Running or Stopped.
    """
    # Retrieve a Docker client
    docker_client = get_docker_client()

    # Perform check
    container_check(docker_client)

    # Get container dicts
    container_status = get_docker_container_status(docker_client)

    # PostGIS
    if container_status[POSTGIS_CONTAINER]:
        print('PostGIS: Running')
    else:
        print('PostGIS: Stopped')

    # GeoServer
    if container_status[GEOSERVER_CONTAINER]:
        print('GeoServer: Running')
    else:
        print('GeoServer: Stopped')

    # 52 North WPS
    if container_status[N52WPS_CONTAINER]:
        print('52 North WPS: Running')
    else:
        print('52 North WPS: Stopped')


def docker_update(container=None, defaults=False):
    """
    Remove Docker containers and pull the latest images updates.
    """
    # Retrieve a Docker client
    docker_client = get_docker_client()

    # Stop containers
    stop_docker_containers(docker_client)

    # Remove containers
    remove_docker_containers(docker_client)

    # Force pull all the images without check to get latest version
    for image in REQUIRED_DOCKER_IMAGES:
        pull_stream = docker_client.pull(image, stream=True)
        log_pull_stream(pull_stream)

    # Reinstall containers
    install_docker_containers(docker_client, force=True)


def docker_ip(container=None, defaults=False):
    """
    Returns the hosts and ports of the Docker containers.
    """
    # Retrieve a Docker client
    docker_client = get_docker_client()

    # Containers
    containers = get_docker_container_dicts(docker_client)
    container_status = get_docker_container_status(docker_client)

    # PostGIS
    if container_status[POSTGIS_CONTAINER]:
        postgis_container = containers[POSTGIS_CONTAINER]
        postgis_port = postgis_container['Ports'][0]['PublicPort']
        print('PostGIS: {0}'.format(postgis_port))

    else:
        print('PostGIS container not running.')

    # GeoServer
    if container_status[GEOSERVER_CONTAINER]:
        geoserver_container = containers[GEOSERVER_CONTAINER]
        geoserver_port = geoserver_container['Ports'][0]['PublicPort']
        print('GeoServer: {0}'.format(geoserver_port))

    else:
        print('GeoServer container not running.')

    # 52 North WPS
    if container_status[N52WPS_CONTAINER]:
        n52wps_container = containers[N52WPS_CONTAINER]
        n52wps_port = n52wps_container['Ports'][0]['PublicPort']
        print('52 North WPS: {0}'.format(n52wps_port))

    else:
        print('52 North WPS container not running.')
