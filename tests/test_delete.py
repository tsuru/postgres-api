# -*- coding: utf-8 -*-

from postgresapi import models, managers, storage
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
                "INSERT INTO instance (name, state, plan) VALUES "
                "('databasenotexist', 'running', 'shared')")
        with db.autocommit() as cursor:
            cursor.execute('CREATE ROLE databaseno_group')
            cursor.execute('CREATE DATABASE databasenotexist '
                           'OWNER databaseno_group')
            cursor.execute('CREATE ROLE databaseno90ae84 '
                           'IN GROUP databaseno_group')
        with self.app.app_context():
            manager = managers.SharedManager()
            manager.delete_instance(
                models.Instance(name='databasenotexist', plan='shared'))

        db = self.create_db()
        with db.transaction() as cursor:
            cursor.execute('SELECT * FROM instance')
            self.assertEqual(cursor.fetchall(), [])
            cursor.execute(
                "SELECT * FROM pg_roles WHERE rolname ='databaseno90ae84'")
            self.assertEqual(cursor.fetchall(), [])

    def test_not_exist(self):
        with self.app.app_context():
            manager = managers.SharedManager()
            self.assertRaises(
                storage.InstanceNotFound, manager.delete_instance,
                models.Instance(name='databasenotexist', plan='shared'))
