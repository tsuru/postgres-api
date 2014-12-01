# -*- coding: utf-8 -*-

from postgresapi import models, managers
from . import _base


class CreateTestCase(_base.TestCase):

    def setUp(self):
        super(CreateTestCase, self).setUp()
        self._drop_test_db()

    def tearDown(self):
        super(CreateTestCase, self).tearDown()
        self._drop_test_db()

    def test_success(self):
        with self.app.app_context():
            manager = managers.SharedManager()
            manager.create_instance('databasenotexist')

        db = self.create_db()
        with db.transaction() as cursor:
            cursor.execute('SELECT name, state, plan FROM instance')
            self.assertEqual(cursor.fetchall(),
                             [('databasenotexist', 'running', 'shared')])

    def test_already_exists(self):
        db = self.create_db()
        manager = managers.SharedManager()

        with db.transaction() as cursor:
            cursor.execute(
                "INSERT INTO instance (name, state, plan) VALUES "
                "('databasenotexist', 'running', 'shared')")
        with self.app.app_context():
            self.assertRaises(managers.InstanceAlreadyExists,
                              manager.create_instance,
                              'databasenotexist')

        with db.autocommit() as cursor:
            cursor.execute('CREATE ROLE databaseno_group')
            cursor.execute('CREATE DATABASE databasenotexist '
                           'OWNER databaseno_group')
        with self.app.app_context():
            self.assertRaises(managers.InstanceAlreadyExists,
                              manager.create_instance,
                              'databasenotexist')
