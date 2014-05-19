# -*- coding: utf-8 -*-

from postgresapi import models
from . import _base


class DeleteTestCase(_base.TestCase):

    def setUp(self):
        super(DeleteTestCase, self).setUp()
        self._drop_test_db()

    def tearDown(self):
        super(DeleteTestCase, self).tearDown()
        self._drop_test_db()

    def test_success(self):
        db = self.create_db()
        with db.transaction() as cursor:
            cursor.execute(
                "INSERT INTO instance (name, state, shared) VALUES "
                "('databasenotexist', 'running', true)")
        with db.autocommit() as cursor:
            cursor.execute('CREATE ROLE databaseno_group')
            cursor.execute('CREATE DATABASE databasenotexist '
                           'OWNER databaseno_group')
        with self.app.app_context():
            models.Instance.delete('databasenotexist')
        db = self.create_db()
        with db.transaction() as cursor:
            cursor.execute('SELECT * FROM instance')
            self.assertEqual(cursor.fetchall(), [])

    def test_not_exist(self):
        with self.app.app_context():
            self.assertRaises(models.InstanceNotFound,
                              models.Instance.delete,
                              'databasenotexist')
