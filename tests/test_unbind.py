# -*- coding: utf-8 -*-

import psycopg2

from postgresapi import managers
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
        user = self.user
        dbname = self.database

        # Connection to the database using app's user credentials
        self.database = 'databasenotexist'
        self.user = 'databaseno90ae84'
        user_db = self.create_db(
            dbname='databasenotexist', user='databaseno90ae84',
            password='59e325e93f6a8aa81e6bfb270c819ccfaaf1e30a')

        # Connection to the same db instance but logging in as main user
        # This will be used to check the table we create is still there
        # when the app is unbound
        self.user = user
        group_db = self.create_db()

        # Reset the username and db name so setUp and tearDown methods work
        self.user = user
        self.database = dbname

        with self.app.app_context():
            manager = managers.SharedManager()
            instance = manager.create_instance('databasenotexist')
            instance.create_user('127.0.0.1')

            # Let's simulate the app creating some objects in the database
            # This could be a Django/Flask app running migrations, for instance
            with user_db.autocommit() as cursor:
                cursor.execute('CREATE TABLE article ('
                               'article_id bigserial primary key, '
                               'article_name varchar(20) NOT NULL, '
                               'article_desc text NOT NULL, '
                               'date_added timestamp default NULL)')
                cursor.execute('INSERT INTO article(article_id, article_name, '
                               'article_desc, date_added) VALUES '
                               "(1, 'hello', 'world world world', NOW())")

            instance.drop_user('127.0.0.1')

        with group_db.transaction() as cursor:
            # The role created after binding the app should be gone
            cursor.execute(
                "SELECT * FROM pg_roles WHERE rolname = 'databaseno90ae84'")
            self.assertEqual(cursor.fetchall(), [])
            # The table created by the app should be still here
            # containing all data
            cursor.execute("SELECT * FROM article")
            self.assertEqual(len(cursor.fetchall()), 1)

    def test_not_found(self):
        with self.app.app_context():
            manager = managers.SharedManager()
            instance = manager.create_instance('databasenotexist')

            self.assertRaises(
                psycopg2.ProgrammingError,
                instance.drop_user,
                '127.0.0.1')
