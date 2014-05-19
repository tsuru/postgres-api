# -*- coding: utf-8 -*-

import psycopg2

from . import _base


class DatabaseTestCase(_base.TestCase):

    def test_ping(self):
        conn = self.create_conn()
        conn.set_isolation_level(0)
        cursor = conn.cursor()
        try:
            cursor.execute('DROP DATABASE databasenotexist')
        except:
            pass
        finally:
            cursor.close()
            conn.close()
        db0 = self.create_db()
        self.assertTrue(db0.ping())
        db1 = self.create_db('databasenotexist')
        self.assertFalse(db1.ping())

    def test_autocommit(self):
        conn = self.create_conn()
        conn.set_isolation_level(0)
        cursor = conn.cursor()
        try:
            cursor.execute('DROP ROLE testuserdonotuse')
        except:
            pass
        finally:
            cursor.close()
            conn.close()
        db = self.create_db()
        with db.autocommit() as cursor:
            cursor.execute('CREATE ROLE testuserdonotuse')
            cursor.execute('DROP ROLE testuserdonotuse')

    def test_transaction(self):
        db0, db1 = self.create_db(), self.create_db()
        conn = self.create_conn()
        cursor = conn.cursor()
        try:
            cursor.execute('DROP TABLE test')
            conn.commit()
        except:
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
        with db0.transaction() as cursor0, \
                db1.transaction() as cursor1:
            cursor0.execute('SELECT 12345')
            self.assertEqual(cursor0.fetchone(), (12345,))
            cursor0.execute('CREATE TABLE test '
                            '(id SERIAL PRIMARY KEY,'
                            ' text VARCHAR(20))')
            for i in xrange(5):
                cursor0.execute("INSERT INTO test (text) VALUES ('test')")
                cursor0.execute('SELECT max(id) FROM test')
                self.assertEqual((i + 1, ), cursor0.fetchone())
            self.assertRaises(psycopg2.ProgrammingError,
                              cursor1.execute,
                              'SELECT id FROM test')
        with db0.transaction() as cursor0, \
                db1.transaction() as cursor1:
            cursor1.execute('SELECT id FROM test'),
            self.assertEqual(
                cursor1.fetchall(),
                [(1,), (2,), (3,), (4,), (5,)])
            # use rollback to unlock table test
            db1.connection.rollback()
            cursor0.execute('DROP TABLE test')
            self.assertRaises(psycopg2.ProgrammingError,
                              cursor0.execute,
                              'SELECT id FROM test')
            cursor1.execute('SELECT id FROM test'),
            self.assertEqual(
                cursor1.fetchall(),
                [(1,), (2,), (3,), (4,), (5,)])
