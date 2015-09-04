# -*- coding: utf-8 -*-
import os
import subprocess
from contextlib import contextmanager

import psycopg2
from psycopg2.extensions import (ISOLATION_LEVEL_AUTOCOMMIT,
                                 ISOLATION_LEVEL_READ_COMMITTED)

_interrupt = (KeyboardInterrupt, SystemExit)


class Database(object):

    def __init__(self, database, user, password, host, port):
        self.user = user
        self.host = host
        self.port = port
        self.password = password
        self.database = database
        self.conn = None

    def connection(self):
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(database=self.database,
                                         user=self.user,
                                         password=self.password,
                                         host=self.host,
                                         port=self.port)
        return self.conn

    @contextmanager
    def transaction(self):
        """Open a "read committed" transaction for SQLs execution"""
        conn = self.connection()
        orig_level = conn.isolation_level
        conn.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.set_isolation_level(orig_level)

    @contextmanager
    def autocommit(self):
        """Execute SQLs in a non-transaction (auto-commit)"""
        conn = self.connection()
        orig_level = conn.isolation_level
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
            conn.set_isolation_level(orig_level)

    def ping(self):
        try:
            with self.transaction() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                return result == (1,)

        except _interrupt:
            raise
        except Exception:
            return False

    def export(self):
        environ = os.environ.copy()
        if self.password:
            environ['PGPASSWORD'] = self.password
        cmd = ["pg_dump", "-U", self.user, self.name]
        return subprocess.check_output(cmd, env=environ)


class AppDatabase(Database):

    def __init__(self, app=None):
        app.db = self
        self.app = app
        self.conn = None

    def connection(self):
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(
                database=self.app.config['POSTGRESQL_DATABASE'],
                user=self.app.config['POSTGRESQL_USER'],
                password=self.app.config['POSTGRESQL_PASSWORD'],
                host=self.app.config['POSTGRESQL_HOST'],
                port=self.app.config['POSTGRESQL_PORT'])
        return self.conn
