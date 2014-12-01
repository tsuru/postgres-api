# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys

from flask.ext.script import Manager

from .apis import app

manager = Manager(app)


def _get_db_revision():
    reversion_ddl = 'CREATE TABLE db_revision (id INTEGER)'
    with app.db.autocommit() as cursor:
        try:
            cursor.execute(reversion_ddl)
        except:
            pass
    with app.db.transaction() as cursor:
        cursor.execute('SELECT id FROM db_revision LIMIT 1')
        ver = cursor.fetchone()
        if ver is None:
            cursor.execute('INSERT INTO db_revision (id) VALUES (0)')
            ver = (0,)
        return ver[0]


def _execute_sqls(basedir, sqls, start_function, stop_function):
    for sql in sqls:
        fname = os.path.join(basedir, sql)
        ver = sql.split('_', 1)[0]

        if not sql.endswith('.sql') or \
                not ver.isdigit() or \
                not start_function(int(ver)):
            continue
        with open(fname) as fp, \
                app.db.autocommit() as cursor:
            cursor.execute(fp.read())
        if stop_function(int(ver)):
            break


@manager.command
def upgrade_db(to_version=None):
    if to_version and not to_version.isdigit():
        print('%s is not a valid version, abort operation' %
              to_version, file=sys.stderr)
        exit(1)
    from_version = _get_db_revision()
    to_version = int(to_version or 0xffffffff)
    sqldir = os.path.join(app.root_path, 'sqls/upgrade')
    sqls = os.listdir(sqldir)
    sqls = filter(lambda sql: sql.split('_')[0].isdigit(), sqls)
    sqls = sorted(sqls, key=lambda sql: int(sql.split('_')[0]))

    def stop_version(ver):
        if ver <= to_version:
            with app.db.transaction() as cursor:
                cursor.execute('UPDATE db_revision SET id=%s', (ver, ))

    _execute_sqls(sqldir, sqls,
                  lambda ver: ver > from_version,
                  stop_version)


@manager.command
def downgrade_db(to_version=None):
    if to_version and not to_version.isdigit():
        print('%s is not a valid version, abort operation' %
              to_version, file=sys.stderr)
        exit(1)
    from_version = _get_db_revision()
    to_version = int(to_version or 0)
    sqldir = os.path.join(app.root_path, 'sqls/downgrade')
    sqls = os.listdir(sqldir)
    sqls = filter(lambda sql: sql.split('_')[0].isdigit(), sqls)
    sqls = sorted(sqls, key=lambda sql: int(sql.split('_')[0]), reverse=True)

    def stop_version(ver):
        if ver > to_version:
            with app.db.transaction() as cursor:
                cursor.execute('UPDATE db_revision SET id=%s', (ver - 1, ))
    _execute_sqls(sqldir, sqls,
                  lambda ver: ver <= from_version,
                  stop_version)
