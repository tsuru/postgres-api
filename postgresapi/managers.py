# -*- coding: utf-8 -*-
from .models import Instance
from .storage import InstanceStorage, InstanceAlreadyExists, InstanceNotFound

import psycopg2

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
    def create_instance(self, name):
        pass

    def delete_instance(self, instance):
        pass