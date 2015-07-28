# -*- coding: utf-8 -*-
import re
import hmac
import hashlib

from flask import current_app as app

from .database import Database


class InvalidInstanceName(Exception):
    def __init__(self, name):
        self.args = ["%s is a invalid name."]


class InvalidInstanceConfiguration(Exception):
    def __init__(self, field):
        self.args = ["%s has not a valid value"]


class DatabaseCreationError(Exception):
    pass


def generate_password(string, host):
    hm = hmac.new(app.config['SALT'], digestmod=hashlib.sha1)
    hm.update(string)
    hm.update(host)
    return hm.hexdigest()


def generate_user(string, host):
    if len(string) > 10:
        string = string[:10]
    string += generate_password(string, host)[:6]
    return string


def generate_group(string):
    if len(string) > 10:
        string = string[:10]
        string += '_group'
    return string


def canonicalize_db_name(name):
    if re.search(r"[\W\s]", name) is not None:
        suffix = hashlib.sha1(name).hexdigest()[:10]
        name = re.sub(r"[\W\s]", "_", name) + suffix
    return name


class ClusterManager(object):

    def __init__(self,
                 host='localhost',
                 port=5432,
                 user='postgres',
                 password='',
                 public_host=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self._public_host = public_host
        self.dbs = {}

    @property
    def public_host(self):
        if self._public_host:
            return self._public_host
        return self.host

    def db(self, name=None):
        if name is None:
            name = 'postgres'  # default database
        if name not in self.dbs:
            self.dbs[name] = Database(name,
                                      self.user,
                                      self.password,
                                      self.host,
                                      self.port)
        return self.dbs[name]

    def create_database(self, name, encoding=None):
        with self.db().autocommit() as cursor:
            grpsql = 'CREATE ROLE %(group)s WITH NOLOGIN'
            dbsql = 'CREATE DATABASE %(name)s'
            ownsql = 'ALTER DATABASE %(name)s OWNER TO %(group)s'
            if encoding is not None:
                dbsql += ' ENCODING %(encoding)s'
            group = generate_group(name)
            context = {'name': name,
                       'group': group,
                       'encoding': encoding}
            cursor.execute(grpsql % context)
            cursor.execute(dbsql % context)
            cursor.execute(ownsql % context)

    def drop_database(self, name):
        group = generate_group(name)

        with self.db().autocommit() as cursor:
            cursor.execute("DROP DATABASE %s" % name)

            # Drop role members first
            cursor.execute("SELECT rolname FROM pg_auth_members pam "
                           "RIGHT JOIN pg_roles pg on pg.oid = pam.member "
                           "WHERE pam.member=pg.oid AND pam.roleid = "
                           "(SELECT oid FROM pg_roles WHERE rolname = '%s');" % group)
            for role_member in list(sum(cursor.fetchall(), ())):
                cursor.execute("DROP ROLE %s" % role_member)

            # Drop parent role
            cursor.execute("DROP ROLE %s" % group)

    def create_user(self, database, host):
        with self.db(database).autocommit() as cursor:
            username = generate_user(database, host)
            password = generate_password(database, host)
            group = generate_group(database)

            # Create the user and inherit privileges from the group role
            sql = "CREATE ROLE %s WITH LOGIN PASSWORD %%s IN ROLE %s"
            cursor.execute(sql % (username, group), (password, ))

            # Alter default privileges will grant objects on group
            sql = "ALTER DEFAULT PRIVILEGES FOR ROLE %s GRANT ALL PRIVILEGES ON %s TO %s"
            for object in ['TABLES', 'SEQUENCES', 'FUNCTIONS']:
                cursor.execute(sql % (username, object, group))

            return username, password

    def drop_user(self, database, host):
        with self.db(database).autocommit() as cursor:
            username = generate_user(database, host)
            group = generate_group(database)

            # Reassign objects back to the group role
            # This is needed to be able to drop an app user role after
            # the app has created some objects in the database (e.g. tables)
            sql = "REASSIGN OWNED BY %s TO %s"
            cursor.execute(sql % (username, group))

            # Remove default privileges from the role
            sql = "ALTER DEFAULT PRIVILEGES FOR ROLE %s REVOKE ALL PRIVILEGES ON %s FROM %s"
            for object in ['TABLES', 'SEQUENCES', 'FUNCTIONS']:
                cursor.execute(sql % (username, object, group))

            cursor.execute("DROP ROLE %s" % username)

    def is_up(self, database):
        return self.db(database).ping()


class Instance(object):
    def __init__(self, name, plan, state='pending', host=None, port=None, container_id=None, username=None,
                 password=None):
        self.name = name
        self.plan = plan
        self.state = state
        self.host = host
        self.port = port
        self.container_id = container_id
        self.username = username
        self.password = password

    def create_user(self, host):
        return self.cluster_manager.create_user(self.name, host)

    def drop_user(self, host):
        return self.cluster_manager.drop_user(self.name, host)

    def get_public_host(self):
        return self.cluster_manager.public_host

    def get_port(self):
        return self.cluster_manager.port

    def is_up(self, database=None):
        if database is None:
            database = self.name

        return self.state == "running" and self.cluster_manager.is_up(database)

    @property
    def cluster_manager(self):
        config = app.config
        if self.plan == 'shared':
            host = config['SHARED_HOST']
            port = config['SHARED_PORT']
            user = config['SHARED_ADMIN']
            password = config['SHARED_ADMIN_PASSWORD']
            public_host = config['SHARED_PUBLIC_HOST']
        elif self.plan == 'dedicated':
            if self.host is None or self.port is None:
                raise InvalidInstanceConfiguration(field=('host' if self.host is None else 'port'))
            elif self.username is None or self.password is None:
                raise InvalidInstanceConfiguration(field='username or password')

            host = public_host = self.host
            port = self.port
            user = self.username
            password = self.password
        else:
            raise NotImplementedError('Currently only shared and dedicated host are supported')

        return ClusterManager(host=host, port=port, user=user, password=password, public_host=public_host)
