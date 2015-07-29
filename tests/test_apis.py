# -*- coding: utf-8 -*-

try:
    import simplejson as json
except ImportError:
    import json

from base64 import b64encode

from postgresapi import models, managers
from . import _base





class ApisTestCase(_base.TestCase):


    def setUp(self):
        super(ApisTestCase, self).setUp()
        self._drop_test_db()
        self._drop_test_user()
        self.client = self.app.test_client()
        self.headers = {
            'Authorization': 'Basic ' + b64encode("{0}:{1}".format('admin', 'password'))
        }

    def tearDown(self):
        super(ApisTestCase, self).tearDown()
        self._drop_test_db()
        self._drop_test_user()

    def test_create_201(self):
        rv = self.client.post('/resources', data={
            'name': 'databasenotexist'
        }, headers=self.headers)
        self.assertEqual(rv.status_code, 201)

    def test_create_400(self):
        rv = self.client.post('/resources',
         headers=self.headers)
        self.assertEqual(rv.status_code, 400)
        rv = self.client.post('/resources', data={
            'name': ''
        }, headers=self.headers)
        self.assertEqual(rv.status_code, 400)

    def test_create_500(self):
        with self.app.app_context():
            manager = managers.SharedManager()
            manager.create_instance('databasenotexist')

        rv = self.client.post('/resources', data={
            'name': 'databasenotexist'
        }, headers=self.headers)
        self.assertEqual(rv.status_code, 500)
        self.assertTrue('already exists' in rv.data)

    def test_bind_app_201(self):
        with self.app.app_context():
            manager = managers.SharedManager()
            manager.create_instance('databasenotexist')

        rv = self.client.post('/resources/databasenotexist/bind-app', data={
            'app-host': '127.0.0.1'
        }, headers=self.headers)
        self.assertEqual(rv.status_code, 201)
        self.assertEqual(json.loads(rv.data), {
            'PG_DATABASE': 'databasenotexist',
            'PG_HOST': 'db.example.com',
            'PG_PASSWORD': '59e325e93f6a8aa81e6bfb270c819ccfaaf1e30a',
            'PG_PORT': '5432',
            'PG_USER': 'databaseno90ae84'
        })

    def test_bind_app_400(self):
        rv = self.client.post('/resources/databasenotexist/bind-app',
             headers=self.headers)
        self.assertEqual(rv.status_code, 400)
        rv = self.client.post('/resources/databasenotexist/bind-app', data={
            'app-host': ''
        }, headers=self.headers)
        self.assertEqual(rv.status_code, 400)

    def test_bind_app_404(self):
        rv = self.client.post('/resources/databasenotexist/bind-app', data={
            'unit-host': '127.0.0.1',
            'app-host': 'testapp.example.com'
        }, headers=self.headers)
        self.assertEqual(rv.status_code, 404)

    def test_bind_app_412(self):
        with self.app.app_context():
            manager = managers.SharedManager()
            manager.create_instance('databasenotexist')

        db = self.create_db()
        with db.transaction() as cursor:
            cursor.execute("UPDATE instance SET state='pending'")
        rv = self.client.post('/resources/databasenotexist/bind-app', data={
            'app-host': '127.0.0.1'
        }, headers=self.headers)
        self.assertEqual(rv.status_code, 412)

    def test_bind_app_500(self):
        with self.app.app_context():
            manager = managers.SharedManager()
            ins = manager.create_instance('databasenotexist')
            ins.create_user('127.0.0.1')

        rv = self.client.post('/resources/databasenotexist/bind-app', data={
            'app-host': '127.0.0.1'
        }, headers=self.headers)
        self.assertEqual(rv.status_code, 500)
        self.assertEqual(rv.data.strip(),
                         'role "databaseno90ae84" already exists')

    def test_unbind_app_200(self):
        with self.app.app_context():
            manager = managers.SharedManager()
            ins = manager.create_instance('databasenotexist')

            ins.create_user('127.0.0.1')
        rv = self.client.delete('/resources/databasenotexist/bind-app', data={
            'app-host': '127.0.0.1'
        }, headers={'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': self.headers['Authorization']})
        self.assertEqual(rv.status_code, 200)

    def test_unbind_app_404(self):
        rv = self.client.delete('/resources/databasenotexist/bind-app', data={
            'app-host': '127.0.0.1'
        }, headers={'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': self.headers['Authorization']})
        self.assertEqual(rv.status_code, 404)

    def test_unbind_app_500(self):
        with self.app.app_context():
            manager = managers.SharedManager()
            manager.create_instance('databasenotexist')

        # the database exists but not the role
        # tsuru's api flow set this to 500 but not 404
        rv = self.client.delete('/resources/databasenotexist/bind-app', data={
            'app-host': '127.0.0.1'
        }, headers={'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': self.headers['Authorization']})
        self.assertEqual(rv.status_code, 500)

        db = self.create_db()
        with db.transaction() as cursor:
            cursor.execute("UPDATE instance SET state='pending'")
        rv = self.client.delete('/resources/databasenotexist/bind-app', data={
            'app-host': '127.0.0.1'
        }, headers={'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': self.headers['Authorization']})
        self.assertEqual(rv.status_code, 500)

    def test_destroy_200(self):
        with self.app.app_context():
            manager = managers.SharedManager()
            manager.create_instance('databasenotexist')

        rv = self.client.delete('/resources/databasenotexist'
            , headers=self.headers)
        self.assertEqual(rv.status_code, 200)

    def test_destroy_404(self):
        rv = self.client.delete('/resources/databasenotexist'
            , headers=self.headers)
        self.assertEqual(rv.status_code, 404)

    def test_status(self):
        rv = self.client.get('/resources/databasenotexist/status'
            , headers=self.headers)
        self.assertEqual(rv.status_code, 404)

        with self.app.app_context():
            manager = managers.SharedManager()
            manager.create_instance('databasenotexist')

        rv = self.client.get('/resources/databasenotexist/status'
            , headers=self.headers)
        self.assertEqual(rv.status_code, 204)

        admin = self.app.config['SHARED_ADMIN']
        self.app.config['SHARED_ADMIN'] = admin * 2
        rv = self.client.get('/resources/databasenotexist/status'
            , headers=self.headers)
        self.assertEqual(rv.status_code, 500)

        self.app.config['SHARED_ADMIN'] = admin
        db = self.create_db()
        with db.transaction() as cursor:
            cursor.execute("UPDATE instance SET state='pending'")
        rv = self.client.get('/resources/databasenotexist/status'
            , headers=self.headers)
        self.assertEqual(rv.status_code, 202)

        with db.transaction() as cursor:
            cursor.execute("UPDATE instance SET state='error'")
        rv = self.client.get('/resources/databasenotexist/status'
            , headers=self.headers)
        self.assertEqual(rv.status_code, 500)

    def test_basic_auth_enabled(self):
        rv = self.client.get('/resources/')
        self.assertEqual(rv.status_code, 401)
        self.assertTrue('WWW-Authenticate' in rv.headers)
        self.assertTrue('Basic' in rv.headers['WWW-Authenticate'])
