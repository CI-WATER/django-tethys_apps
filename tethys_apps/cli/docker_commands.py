import subprocess
from subprocess import Popen, PIPE
import os
import sys
import time
import json
from functools import cmp_to_key
from docker.utils import kwargs_from_env, compare_version
from docker.client import Client as DockerClient, DEFAULT_DOCKER_API_VERSION as MAX_CLIENT_DOCKER_API_VERSION

__all__ = ['docker_init', 'docker_start', 'docker_stop', 'docker_refresh', 'docker_status', 'docker_update']

MINIMUM_API_VERSION = '1.14'

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

    except:
        print("TODO: NEED TO HANDLE LINUX AND WINDOWS CASES in docker_commands.py get_docker_client()")
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


def docker_init():
    """
    Pull Docker images for Tethys Platform and Run for the first time, prompting for various input parameters.
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

    # Check for containers that need to be created
    containers_to_create = get_containers_to_create(docker_client)

    # PostGIS
    if POSTGIS_CONTAINER in containers_to_create:
        print("Installing the PostGIS Docker container...")

        postgis_container = docker_client.create_container(name=POSTGIS_CONTAINER,
                                                           image=POSTGIS_IMAGE,
                                                           environment={'TETHYS_DEFAULT_PASS': 'pass',
                                                                        'TETHYS_DB_MANAGER_PASS': 'pass',
                                                                        'TETHYS_SUPER_PASS': 'pass'}
        )

    else:
        print("PostGIS Docker container already installed: skipping.")

    # GeoServer
    if GEOSERVER_CONTAINER in containers_to_create:
        print("Installing the GeoServer Docker container...")

        geoserver_container = docker_client.create_container(name=GEOSERVER_CONTAINER,
                                                             image=GEOSERVER_IMAGE
        )

    else:
        print("GeoServer Docker container already installed: skipping.")

    # 52 North WPS
    if N52WPS_CONTAINER in containers_to_create:
        print("Installing the 52 North WPS Docker container...")

        wps_container = docker_client.create_container(name=N52WPS_CONTAINER,
                                                       image=N52WPS_IMAGE,
                                                       environment={'NAME': '',
                                                                    'POSITION': '',
                                                                    'ADDRESS': '',
                                                                    'CITY': '',
                                                                    'STATE': '',
                                                                    'COUNTRY': '',
                                                                    'POSTAL_CODE': '',
                                                                    'EMAIL': '',
                                                                    'PHONE': '',
                                                                    'FAX': '',
                                                                    'USERNAME': 'wps',
                                                                    'PASSWORD': 'wps'
                                                                    }
        )

    else:
        print("52 North WPS Docker container already installed: skipping.")


def docker_start():
    print('start')


def docker_stop():
    print('stop')


def docker_refresh():
    print('refresh')


def docker_status():
    print('status')


def docker_update():
    print('update')


