# -*- coding: utf-8 -*-

import psycopg2

from postgresapi import models, managers
from . import _base


class UnbindTestCase(_base.TestCase):

    def setUp(self):
        super(UnbindTestCase, self).setUp()
        self._drop_test_db()
        self._drop_test_user()

    def tearDown(self):
        super(UnbindTestCase, self).tearDown()
        self._drop_test_db()
        self._drop_test_user()

    def test_success(self):
        db = self.create_db()
        with db.autocommit() as cursor:
            cursor.execute('CREATE ROLE databaseno90ae84')
        with self.app.app_context():
            manager = managers.SharedManager()
            instance = manager.create_instance('databasenotexist')
            instance.drop_user('127.0.0.1')

    def test_not_found(self):
        with self.app.app_context():
            manager = managers.SharedManager()
            instance = manager.create_instance('databasenotexist')

            self.assertRaises(
                psycopg2.ProgrammingError,
                instance.drop_user,
                '127.0.0.1')
