# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys

import unittest
import psycopg2

from postgresapi import app, manage, database


class TestCase(unittest.TestCase):

    def setUp(self):
        self.database = database = os.environ.get('TEST_PG_DATABASE',
                                                  'postgres_test')
        self.user = user = os.environ.get('TEST_PG_USER', 'postgres')
        self.password = password = os.environ.get('TEST_PG_PASSWORD', '')
        self.host = host = os.environ.get('TEST_PG_HOST', 'localhost')
        self.port = port = int(os.environ.get('TEST_PG_PORT', '5432'))
        try:
            conn = psycopg2.connect(database=database,
                                    user=user,
                                    password=password,
                                    host=host,
                                    port=port)
            conn.close()
        except:
            print('Can not connection to PostgreSQL database '
                  '"db://%s:%s@%s:%s/%s". \n'
                  'Use theses environment variables to specify '
                  'connection parameters:\n'
                  ' - TEST_PG_DATABSE (default: postgres_test)\n'
                  ' - TEST_PG_USER (default: postgres)\n'
                  ' - TEST_PG_PASSWORD (default: <empty string>)\n'
                  ' - TEST_PG_HOST (default: localhost)\n'
                  ' - TEST_PG_PORT (default: 5432)' %
                  (user, password, host, port, database), file=sys.stderr)
            exit(1)
        app.config.update(dict(
            POSTGRESQL_DATABASE=database,
            POSTGRESQL_USER=user,
            POSTGRESQL_PASSWORD=password,
            POSTGRESQL_HOST=host,
            POSTGRESQL_PORT=port,
            SHARED_HOST=host,
            SHARED_PORT=port,
            SHARED_ADMIN=user,
            SHARED_ADMIN_PASSWORD=password,
            SHARED_PUBLIC_HOST='db.example.com',
            SALT='f0dcb6e03d67149f06ca7865a34e2355d619dcf7'))
        self.app = app
        manage.upgrade_db()

    def tearDown(self):
        manage.downgrade_db()

    def create_conn(self):
        return psycopg2.connect(
            database=self.database, user=self.user,
            password=self.password, host=self.host, port=self.port)

    def create_db(self, dbname=None):
        return database.Database(
            dbname or self.database, self.user,
            self.password, self.host, self.port)

    def _drop_test_db(self):
        db = self.create_db()
        with db.autocommit() as cursor:
            try:
                cursor.execute('DROP DATABASE databasenotexist')
            except:
                pass
            try:
                cursor.execute('DROP ROLE databaseno_group')
            except:
                pass

    def _drop_test_user(self):
        db = self.create_db()
        with db.autocommit() as cursor:
            try:
                cursor.execute('DROP USER databasenofdbf8d')
            except:
                pass
