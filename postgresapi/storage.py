# -*- coding: utf-8 -*-
from flask import current_app as app
from .models import Instance

class InstanceNotFound(Exception):
    def __init__(self, name):
        self.args = ["Instance %s is not found." % name]

class InstanceAlreadyExists(Exception):
    def __init__(self, name):
        self.args = ["Instance %s already exists." % name]


class InstanceStorage(object):
    def __init__(self, table_name='instance'):
        self.table_name = table_name

    def instance_by_name(self, name):
        with app.db.transaction() as cursor:
            cursor.execute('SELECT name, plan, state FROM %s WHERE name=%%s' % self.table_name, (name, ))

            try:
                name, plan, state = cursor.fetchone()

            except TypeError:
                raise InstanceNotFound(name=name)

            return Instance(name, plan, state)

    def instance_exists(self, name):
        with app.db.transaction() as cursor:
            cursor.execute('SELECT 1 FROM %s WHERE name=%%s' % self.table_name, (name, ))
            return True if cursor.fetchone() else False

    def store(self, instance):
        with app.db.transaction() as cursor:
            cursor.execute(
                'INSERT INTO %s (name, plan, state) VALUES (%%s, %%s, %%s)' % self.table_name,
                (instance.name, instance.plan, instance.state)
            )

    def delete_by_name(self, name):
        with app.db.transaction() as cursor:
            cursor.execute('DELETE FROM %s WHERE name=%%s' % self.table_name, (name, ))
