# -*- coding: utf-8 -*-

import psycopg2

from postgresapi import models
from . import _base


class BindTestCase(_base.TestCase):

    def setUp(self):
        super(BindTestCase, self).setUp()
        self._drop_test_db()
        self._drop_test_user()

    def tearDown(self):
        super(BindTestCase, self).tearDown()
        self._drop_test_db()
        self._drop_test_user()

    def test_success(self):
        with self.app.app_context():
            models.Instance.create('databasenotexist')
            instance = models.Instance.retrieve('databasenotexist')
            user, password = instance.create_user('127.0.0.1')
            self.assertEqual(user, 'databaseno90ae84')
            self.assertEqual(password,
                             '59e325e93f6a8aa81e6bfb270c819ccfaaf1e30a')

    def test_already_exists(self):
        db = self.create_db()
        with db.autocommit() as cursor:
            cursor.execute('CREATE ROLE databaseno90ae84')
        with self.app.app_context():
            models.Instance.create('databasenotexist')
            instance = models.Instance.retrieve('databasenotexist')
            self.assertRaises(
                psycopg2.ProgrammingError,
                instance.create_user,
                '127.0.0.1')
