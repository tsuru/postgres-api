# -*- coding: utf-8 -*-

import psycopg2
from postgresapi import plans
from postgresapi.models import canonicalize_db_name, Instance

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

    def test_instance(self):
        with self.app.app_context():
            db_name = canonicalize_db_name('testing')
            manager = plans.get_manager_by_plan('shared')

            con = self.create_conn()
            con.set_isolation_level(0)
            cursor = con.cursor()
            try:
                cursor.execute('DROP DATABASE testing')
                cursor.execute('DROP ROLE testing')
                con.commit()
            except:
                pass
            finally:
                cursor.close()
                con.close()

            instance = manager.create_instance(db_name)
            self.database = db_name

            try:
                self.user, self.password = instance.create_user('first')

                first_con = self.create_conn()
                cursor = first_con.cursor()

                try:
                    cursor.execute('CREATE TABLE test(name text)')
                    first_con.commit()
                    cursor.execute('INSERT INTO test VALUES (\'test\')')
                    first_con.commit()

                    self.user, self.password = instance.create_user('second')
                    second_con = self.create_conn()
                    second_cursor = second_con.cursor()

                    try:
                        second_cursor.execute('SELECT name FROM test')
                        second_cursor.fetchall()
                    except:
                        second_con.rollback()
                        raise
                    finally:
                        second_cursor.close()
                        second_con.close()
                except:
                    first_con.rollback()
                    raise
                finally:
                    cursor.execute('DROP TABLE test')
                    first_con.commit()
                    cursor.close()
                    first_con.close()
            except:
                raise
            finally:
                instance.drop_user('first')
                instance.drop_user('second')
