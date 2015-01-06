#!/bin/bash

# start up a celery instance
if [ "$1" = 'celery' ]; then
    echo "[Run] Starting celery"

    chown -R celery:celery /app

    if [[ -z "$CELERY_CONFIG_MODULE" ]] ; then
        CELERY_CONFIG_MODULE="settings"
    fi
    if [[ -z "$CELERYD_CHDIR" ]] ; then
        CELERYD_CHDIR=`pwd`
    fi
    if [[ -z "$CELERY_BROKER" ]] ; then
        CELERY_BROKER="amqp://guest:guest@mq:5672//"
    fi
    if [[ -z "$CELERY_APP" ]] ; then
        CELERY_APP="app.celerytasks"
    fi
    if [[ -z "$CELERY_LOGLEVEL" ]] ; then
        CELERY_LOGLEVEL="DEBUG"
    fi
    if [[ -z "$CELERY_OPTIMIZATION" ]] ; then
        CELERY_OPTIMIZATION="fair"
    fi
    if [[ -z "$CELERY_AUTORELOAD" ]] ; then
        CELERY_AUTORELOAD=""
    else
        CELERY_AUTORELOAD="--autoreload"
    fi
    if [[ -z "$CELERY_OPTS" ]] ; then
        CELERY_OPTS="-A ${CELERY_APP} -E --loglevel=${CELERY_LOGLEVEL} -O${CELERY_OPTIMIZATION} -b ${CELERY_BROKER} ${CELERY_AUTORELOAD}"
    fi
    if [[ -z "$DJANGO_SETTINGS_MODULE" ]] ; then
        DJANGO_SETTINGS_MODULE="django.settings"
    fi
    if [[ -z "$DJANGO_PROJECT_DIR" ]] ; then
        DJANGO_PROJECT_DIR="${CELERYD_CHDIR}"
    fi
    if [[ -z "$PROJECT_DIRECTORY" ]] ; then
        PROJECT_DIRECTORY="${CELERYD_CHDIR}"
    fi

    echo "CELERY_CONFIG_MODULE is ${CELERY_CONFIG_MODULE}"
    echo "CELERYD_CHDIR is ${CELERYD_CHDIR}"
    echo "CELERY_BROKER is ${CELERY_BROKER}"
    echo "CELERY_APP is ${CELERY_APP}"
    echo "CELERY_LOGLEVEL is ${CELERY_LOGLEVEL}"
    echo "CELERY_OPTIMIZATION is ${CELERY_OPTIMIZATION}"
    echo "CELERY_AUTORELOAD is ${CELERY_AUTORELOAD}"
    echo "CELERY_OPTS is ${CELERY_OPTS}"
    echo "DJANGO_SETTINGS_MODULE is ${DJANGO_SETTINGS_MODULE}"
    echo "DJANGO_PROJECT_DIR is ${DJANGO_PROJECT_DIR}"
    echo "PROJECT_DIRECTORY is ${PROJECT_DIRECTORY}"
     
    export CELERY_CONFIG_MODULE DJANGO_SETTINGS_MODULE DJANGO_PROJECT_DIR PROJECT_DIRECTORY CELERYD_CHDIR

    if [[ -z "$DEPLOYMENT" ]] ; then
        DEPLOYMENT="dev"
    fi
    if [[ -z "$PRODUCTION" ]] ; then
        PRODUCTION=0
    fi
    if [[ -z "$DEBUG" ]] ; then
        DEBUG=1
    fi
    if [[ -z "$DBSERVER" ]] ; then
        DBSERVER="db"
    fi
    if [[ -z "$MEMCACHE" ]] ; then
        MEMCACHE="cache:11211"
    fi

    echo "DEPLOYMENT is ${DEPLOYMENT}"
    echo "PRODUCTION is ${PRODUCTION}"
    echo "DEBUG is ${DEBUG}"
    echo "DBSERVER is ${DBSERVER}"
    echo "MEMCACHE is ${MEMCACHE}"
    
    export DEPLOYMENT PRODUCTION DEBUG DBSERVER MEMCACHE

    gosu celery /usr/local/bin/celery worker ${CELERY_OPTS}
    exit $?
fi

# start up a uwsgi instance
if [ "$1" = 'uwsgi' ]; then
    echo "[Run] Starting uwsgi"

    if [[ -z "$UWSGI_OPTS" ]] ; then
        UWSGI_OPTS="/app/uwsgi/docker.ini"
    fi

    echo "UWSGI_OPTS is ${UWSGI_OPTS}"

    /usr/local/bin/uwsgi ${UWSGI_OPTS}
    exit $?
fi

# start up a runserver instance
if [ "$1" = 'runserver' ]; then
    echo "[Run] Starting runserver"

    if [[ -z "$DEPLOYMENT" ]] ; then
        DEPLOYMENT="dev"
    fi
    if [[ -z "$PRODUCTION" ]] ; then
        PRODUCTION=0
    fi
    if [[ -z "$DEBUG" ]] ; then
        DEBUG=1
    fi
    if [[ -z "$DBSERVER" ]] ; then
        DBSERVER="db"
    fi
    if [[ -z "$MEMCACHE" ]] ; then
        MEMCACHE="cache:11211"
    fi
    if [[ -z "$CELERY_BROKER" ]] ; then
        CELERY_BROKER="amqp://guest:guest@mq:5672//"
    fi

    echo "DEPLOYMENT is ${DEPLOYMENT}"
    echo "PRODUCTION is ${PRODUCTION}"
    echo "DEBUG is ${DEBUG}"
    echo "DBSERVER is ${DBSERVER}"
    echo "MEMCACHE is ${MEMCACHE}"
    echo "CELERY_BROKER is ${CELERY_BROKER}"

    export DEPLOYMENT PRODUCTION DEBUG DBSERVER MEMCACHE CELERY_BROKER

    if [[ -z "$RUNSERVER_PORT" ]] ; then
        RUNSERVER_PORT="8000"
    fi
    if [[ -z "$DJANGO_SETTINGS_MODULE" ]] ; then
        DJANGO_SETTINGS_MODULE="django.settings"
    fi

    if [[ -z "$RUNSERVER_OPTS" ]] ; then
        RUNSERVER_OPTS="runserver_plus 0.0.0.0:${RUNSERVER_PORT} --settings=${DJANGO_SETTINGS_MODULE}"
    fi

    echo "RUNSERVER_PORT is ${RUNSERVER_PORT}"
    echo "DJANGO_SETTINGS_MODULE is ${DJANGO_SETTINGS_MODULE}"
    echo "RUNSERVER_OPTS is ${RUNSERVER_OPTS}"

    django-admin.py syncdb --noinput --settings=${DJANGO_SETTINGS_MODULE}
    django-admin.py migrate --noinput --settings=${DJANGO_SETTINGS_MODULE}
    django-admin.py ${RUNSERVER_OPTS}
    exit $?
fi

echo "[RUN]: Builtin command not provided [runserver|celery|uwsgi]"
echo "[RUN]: $@"

exec "$@"
