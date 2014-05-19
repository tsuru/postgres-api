# -*- coding: utf-8 -*-

from postgresapi import models
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
            models.Instance.create('databasenotexist')
        db = self.create_db()
        with db.transaction() as cursor:
            cursor.execute('SELECT * FROM instance')
            self.assertEqual(cursor.fetchall(),
                             [('databasenotexist', 'running', True)])

    def test_already_exists(self):
        db = self.create_db()
        with db.transaction() as cursor:
            cursor.execute(
                "INSERT INTO instance (name, state, shared) VALUES "
                "('databasenotexist', 'running', true)")
        with self.app.app_context():
            self.assertRaises(models.InstanceAlreadyExists,
                              models.Instance.create,
                              'databasenotexist')

        with db.autocommit() as cursor:
            cursor.execute('CREATE ROLE databaseno_group')
            cursor.execute('CREATE DATABASE databasenotexist '
                           'OWNER databaseno_group')
        with self.app.app_context():
            self.assertRaises(models.InstanceAlreadyExists,
                              models.Instance.create,
                              'databasenotexist')
