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
            cursor.execute('SELECT name, plan, state, host, port, container_id, admin_user, admin_password'
                           ' FROM %s WHERE name=%%s' % self.table_name, (name, ))

            try:
                return self.instance_from_row(cursor.fetchone())

            except TypeError:
                raise InstanceNotFound(name=name)

    def find_instances_by_host(self, host):
        with app.db.transaction() as cursor:
            cursor.execute('SELECT name, plan, state, host, port, container_id, admin_user, admin_password '
                           'FROM %s WHERE host=%%s' % self.table_name, (host, ))

            instances = []
            for record in cursor:
                instances.append(self.instance_from_row(record))

            return instances

    def instance_from_row(self, row):
        return Instance(
            name=row[0],
            plan=row[1],
            state=row[2],
            host=row[3],
            port=row[4],
            container_id=row[5],
            username=row[6],
            password=row[7]
        )

    def instance_exists(self, name):
        with app.db.transaction() as cursor:
            cursor.execute('SELECT 1 FROM %s WHERE name=%%s' % self.table_name, (name, ))
            return True if cursor.fetchone() else False

    def store(self, instance):
        with app.db.transaction() as cursor:
            if self.instance_exists(instance.name):
                cursor.execute(
                    'UPDATE %s SET plan = %%s, state = %%s, host = %%s, port = %%s, container_id = %%s,'
                    ' admin_user = %%s, admin_password = %%s WHERE name = %%s' % self.table_name,
                    (instance.plan, instance.state, instance.host, instance.port, instance.container_id,
                     instance.username, instance.password, instance.name)
                )
            else:
                cursor.execute(
                    'INSERT INTO %s (name, plan, state, host, port, container_id, admin_user, admin_password) '
                    'VALUES (%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s)' % self.table_name,
                    (instance.name, instance.plan, instance.state, instance.host, instance.port, instance.container_id,
                     instance.username, instance.password)
                )

    def delete_by_name(self, name):
        with app.db.transaction() as cursor:
            cursor.execute('DELETE FROM %s WHERE name=%%s' % self.table_name, (name, ))
