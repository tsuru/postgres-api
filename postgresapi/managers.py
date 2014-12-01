# -*- coding: utf-8 -*-
from .models import Instance, generate_password, generate_user
from .storage import InstanceStorage, InstanceAlreadyExists, InstanceNotFound
from flask import current_app as app

import psycopg2
import docker
import time
from urlparse import urlparse


class DockerUnexpectedResponse(Exception):
    def __init__(self, response):
        self.args = ["Unexpected response: %s" % repr(response)]


class DockerImageNotFound(Exception):
    def __init__(self, image):
        self.args = ["Docker image %s is not found"]


class DockerContainerError(Exception):
    pass


class BaseManager(object):
    def __init__(self):
        self.storage = InstanceStorage()

    def register_instance(self):
        pass


class SharedManager(BaseManager):
    def create_instance(self, name):
        if self.storage.instance_exists(name):
            raise InstanceAlreadyExists(name=name)

        instance = Instance(name, 'shared')

        try:
            instance.cluster_manager.create_database(instance.name)
        except psycopg2.ProgrammingError as e:
            if e.args and 'already exists' in e.args[0]:
                raise InstanceAlreadyExists(name=instance.name)

            raise e

        instance.state = 'running'

        self.storage.store(instance)
        return instance

    def delete_instance(self, instance):
        if not self.storage.instance_exists(instance.name):
            raise InstanceNotFound(name=instance.name)

        instance.cluster_manager.drop_database(instance.name)

        self.storage.delete_by_name(instance.name)


class DedicatedManager(BaseManager):
    def __init__(self):
        super(DedicatedManager, self).__init__()

        self.docker_host = app.config["DOCKER_HOST"]
        self.port_range_start = app.config["DEDICATED_PORT_RANGE_START"]
        self.image_name = app.config["DEDICATED_IMAGE_NAME"]

    def client(self, host=None):
        if host is None:
            host = self.docker_host

        return docker.Client(base_url=host)

    def extract_hostname(self, url):
        return urlparse(url).hostname

    def get_port_by_host(self, host):
        storage = InstanceStorage()
        instances = storage.find_instances_by_host(host)

        if instances:
            ports = []
            for instance in instances:
                if instance.port is not None:
                    ports.append(int(instance.port))

            return max(ports) + 1

        return self.port_range_start

    def create_instance(self, name):
        if self.storage.instance_exists(name):
            raise InstanceAlreadyExists(name=name)

        client = self.client()
        host = self.extract_hostname(client.base_url)
        port = self.get_port_by_host(host)
        admin_user = generate_user(name, host)
        admin_password = generate_password(name, host)

        try:
            output = client.create_container(
                self.image_name,
                command="",
                ports=[5432],
                environment={
                    "POSTGRES_USER": admin_user,
                    "POSTGRES_PASSWORD": admin_password
                }
            )
        except docker.APIError as e:
            if e.response.status_code == 404:
                raise DockerImageNotFound(image=self.image_name)
            else:
                raise DockerUnexpectedResponse(response=e.response)

        instance = Instance(
            name=name,
            plan='dedicated',
            host=host,
            port=port,
            container_id=output["Id"],
            username=admin_user,
            password=admin_password
        )
        self.storage.store(instance)

        try:
            client.start(output["Id"], port_bindings={5432: ('0.0.0.0', port)})
        except docker.APIError as e:
            raise DockerUnexpectedResponse(response=e.response.content)

        instance.state = 'running'
        self.storage.store(instance)

        if not self.is_up(instance, 30):
            raise DockerContainerError('Instance not up after %d tries with (%s/%s)' % (30, admin_user, admin_password))

        instance.cluster_manager.create_database(name)
        self.storage.store(instance)

        return instance

    def is_up(self, instance, max_try=3):
        while max_try > 0:
            if instance.is_up(instance.username):
                return True
            else:
                time.sleep(1)
                max_try -= 1

        return False

    def delete_instance(self, instance):
        client = self.client()
        client.stop(instance.container_id)
        client.remove_container(instance.container_id)

        self.storage.delete_by_name(instance.name)
