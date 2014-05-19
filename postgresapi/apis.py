# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify

from .database import AppDatabase
from .models import Instance, InstanceNotFound

app = Flask('postgresapi')
app.config.from_pyfile('application.cfg')
AppDatabase(app)


@app.errorhandler(500)
def internal_server_error(e):
    if e.args:
        return e.args[-1], 500
    else:
        return 'Unknown internal server error', 500


@app.route("/resources", methods=["POST"])
def create_instance():
    """create a new database

    $ tsuru service-add postgres postgres_instance

    Possible HTTP status codes:

    * 201: database is successfully created
    * 400: bad request, check your query
    * 500: creation process is failed

    """
    if 'name' not in request.form:
        return 'Parameter `name` is missing', 400
    name = request.form['name']
    if not name:
        return 'Parameter `name` is empty', 400
    Instance.create(name)
    return '', 201


@app.route("/resources/<name>", methods=["POST"])
def bind_app(name):
    """Bind an app user to the database

    $ tsuru bind postgres_instance --app my_app

    Possible HTTP status codes:

    * 201: database user is successfully created, with these environment
      variables are returned:
      - PG_HOST
      - PG_PORT
      - PG_DATABASE
      - PG_USER
      - PG_PASSWORD
    * 400: bad request, check your query
    * 404: database does not exist
    * 412: database is not ready
    * 500: user creation process is failed

    """
    if 'hostname' not in request.form:
        return 'Parameter `hostname` is missing', 400
    hostname = request.form['hostname']
    if not hostname:
        return 'Parameter `hostname` is empty', 400
    try:
        instance = Instance.retrieve(name)
    except InstanceNotFound:
        return 'Instance `%s` is not found' % name, 404
    if instance.state != 'running':
        return 'Can\'t bind to this instance because it\'s not running', 412
    username, password = instance.create_user(hostname)
    config = {
        'PG_HOST': instance.public_host,
        'PG_PORT': instance.port,
        'PG_DATABASE': instance.name,
        'PG_USER': username,
        'PG_PASSWORD': password}
    return jsonify(config), 201


@app.route("/resources/<name>/hostname/<hostname>", methods=["DELETE"])
def unbind_app(name, hostname):
    """Unbind an app user from the database

    $ tsuru unbind postgres_instance --app my_app

    Possible HTTP status codes:

    * 200: database user is successfully dropped or does not exist
    * 404: database does not exist
    * 500: user dropping process is failed

    """
    try:
        instance = Instance.retrieve(name)
    except InstanceNotFound:
        return 'Instance `%s` is not found' % name, 404
    if instance.state != 'running':
        return ('Can\'t unbind from this instance '
                'because it\'s not running'), 500
    instance.drop_user(hostname)
    return '', 200


@app.route("/resources/<name>", methods=["DELETE"])
def destroy_instance(name):
    """Destroy an database

    $ tsuru service-remove postgres_instance

    Possible HTTP status codes:

    * 200: database is successfully dropped
    * 404: database does not exist
    * 500: dropping process is failed

    """
    try:
        Instance.delete(name)
    except InstanceNotFound:
        return 'Can\'t drop `%s` because it doesn\'t exist' % name, 404
    return '', 200


@app.route("/resources/<name>/status", methods=["GET"])
def status(name):
    """Check instance status

    $ tsuru service-status postgres_instance

    Possible HTTP status codes:

    * 202: database is pending
    * 204: database is running and ready for connections
    * 500: database is stopped for some reason

    """
    try:
        instance = Instance.retrieve(name)
    except InstanceNotFound:
        return 'Instance `%s` is not found' % name, 404
    if instance.state == 'pending':
        return instance.state, 202
    elif instance.is_up():
        return '', 204
    return '', 500
