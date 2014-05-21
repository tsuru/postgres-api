tsuru-postgresapi
=================

A PostgreSQL API for tsuru PaaS

[![Build Status](https://travis-ci.org/guokr/tsuru-postgresapi.svg?branch=master)](https://travis-ci.org/guokr/tsuru-postgresapi)


Installation
------------

### Install PostgreSQL server (Debian/Ubuntu)

First you should have a PostgreSQL server. In Debian/Ubuntu, use `apt-get` to install it.

```bash
$ sudo apt-get install postgresql
```

#### Create database for postgresapi

After install PostgreSQL, you need to create a user and a database for `postgresapi`. Here is an example:

```bash
$ sudo -u postgres createuser postgresapi -P
# "Enter password for new role"
# "Enter it again"
# "Shall the new role be a superuser?" No
# "Shall the new role be allowed to create databases?", No
# "Shall the new role be allowed to create more new roles?", No

$ sudo -u postgres createdb postgresapi -O postgresapi
```

#### Create superuser to manage databases

You can use another host to provide PostgreSQL to other applications.

```bash
$ sudo -u postgres createuser postgresadmin -P
# "Enter password for new role"
# "Enter it again"
# "Shall the new role be a superuser?" Yes
```

#### Access control

You may have to edit server's `pg_hba.conf` and `postgresql.conf` to allow accessing from external IPs. See PostgreSQL's document for more.

```bash
# change "9.3" to the version of your current PostgreSQL cluster

# add this line (change "10.0.2.0/24" to the allowed CIDR):
# host    all    all    10.0.2.0/24    md5
$ sudo editor /etc/postgresql/9.3/main/pg_hba.conf

# change "listen_addresses" to "0.0.0.0" to listen on all interfaces
$ sudo editor /etc/postgresql/9.3/main/postgresql.conf

$ sudo service postgresql restart
```

### Install service

Now you can install `postgresapi` service. In your tsuru client machine (with crane installed):

```bash
$ git clone https://github.com/guokr/tsuru-postgresapi
$ tsuru app-create postgresapi python
```

Export these environment variables:

```bash
# postgresapi's database configure
$ tsuru env-set -a postgresapi POSTGRESAPI_DATABASE=postgresapi
$ tsuru env-set -a postgresapi POSTGRESAPI_USER=postgresapi
$ tsuru env-set -a postgresapi POSTGRESAPI_PASSWORD=******
$ tsuru env-set -a postgresapi POSTGRESAPI_HOST=localhost
$ tsuru env-set -a postgresapi POSTGRESAPI_PORT=5432

# salt used to hash the username/password
$ tsuru env-set -a postgresapi POSTGRESAPI_SALT=******
```

We are only support shared mode currently. Export these variables to specify the shared cluster:

```bash
# these settings can be different with postgresapi's database
$ tsuru env-set -a postgresapi POSTGRESAPI_SHARED_HOST=localhost
$ tsuru env-set -a postgresapi POSTGRESAPI_SHARED_PORT=5432
$ tsuru env-set -a postgresapi POSTGRESAPI_SHARED_ADMIN=postgresadmin
$ tsuru env-set -a postgresapi POSTGRESAPI_SHARED_ADMIN_PASSWORD=******
$ tsuru env-set -a postgresapi POSTGRESAPI_SHARED_PUBLIC_HOST=pg.example.com
```

Configuration are finished now. Deploy the service.

```bash
# Find out git repository then deploy the service
$ cd tsuru-postgresapi
$ tsuru app-info -a postgresapi | grep Repository
$ git remote add tsuru git@tsuru.example.com:postgresapi.git
$ git push tsuru master

# The database is ready. Upgrade it!
$ tsuru run --app postgresapi -- python manage.py upgrade_db
```

Configure the service template and point it to your application:

```bash
$ cp service.yaml.example service.yaml
# you can find out production address from app-info
$ tsuru app-info -a postgresapi | grep Address
# set production address
$ editor service.yaml
$ crane create service.yaml
```

To list your services:

```bash
$ crane list
# OR
$ tsuru service-list
```


Usage
-----

Please see [tsuru's document](http://docs.tsuru.io/en/latest/services/api.html).


TODO
----

1. Provision mode
2. EC2 supporting
3. Handle database connection timeout
