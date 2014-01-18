import os
from setuptools import setup

packages = ['yabiadmin'] + ['yabiadmin.%s' % app for app in ['yabifeapp', 'yabistoreapp', 'yabiengine', 'yabi', 'uploader', 'preview', 'registration', 'backend']] + ['yabiadmin.yabi.migrations', 'yabiadmin.yabi.migrationutils', 'yabiadmin.yabiengine.migrations', 'yabiadmin.yabi.templatetags']

data_files = {}
start_dir = os.getcwd()
for package in packages:
    data_files[package] = []
    path = package.replace('.', '/')
    os.chdir(path)
    for data_dir in ('templates', 'static', 'migrations', 'fixtures'):
        data_files[package].extend(
            [os.path.join(subdir, f) for (subdir, dirs, files) in os.walk(data_dir) for f in files])
    os.chdir(start_dir)

install_requires = [
    'Django==1.5.4',
    # pip > 1.4 doesn't pick up pytz, because of non-standard version number
    # Bug is still under discussion: https://bugs.launchpad.net/pytz/+bug/1204837
    'pytz>=2013b',
    'ccg-webservices==0.1.2',
    'ccg-registration==0.8-alpha-1',
    'ccg-makoloader==0.2.6',
    'ccg-introspect==0.1.2',
    'ccg-extras==0.1.7',
    'ccg-auth==0.3.3',
    'anyjson==0.3.3',
    'SQLAlchemy>=0.7.10,<0.8.0',
    'celery>=3.0.22,<3.1.0',
    'amqplib==1.0.2',
    'django-celery>=3.0.17,<3.1.0',
    'kombu>=2.5.13,<2.6.0',
    'billiard>=2.7.3.32,<2.8.0.0',
    'django-templatetag-sugar==0.1',
    'ordereddict==1.1',
    'python-memcached>=1.53,<2.0',
    'Mako==0.5.0',
    'South==0.7.6',
    'django-extensions>=1.2.0,<1.2.0',
    'beautifulsoup4>=4.3.2,<4.4.0',
    'lxml>=3.2.0,<3.3.0',
    'cssutils>=0.9.10,<0.10.0',
    'httplib2>=0.8,<0.9',
    'djamboloader==0.1.2',
    'paramiko>=1.10.0,<1.11.0',
    'boto==2.13.3',
    'python-dateutil>=2.1,<3.0',
    'yaphc==0.1.5',
    'pycrypto==2.6.1',  # version locked as a 2.7a1 appeared in pypi
    'six>=1.4,<1.5',
]

dev_requires = [
    'flake8>=2.0,<2.1',
    'flower>=0.5',
    'Werkzeug',
    'gunicorn',
]

tests_require = [
    'requests==1.2.0',
    'django-nose',
    'nose==1.2.1',
    'mockito>=0.5.0,<0.6.0',
]

postgresql_requires = [
    'psycopg2>=2.5.0,<2.6.0',
]

mysql_requires = [
    'MySQL-python>=1.2.0,<1.3.0',
]

dependency_links = [
    'https://ccg-django-extras.googlecode.com/files/ccg-webservices-0.1.2.tar.gz',
    'https://ccg-django-extras.googlecode.com/files/ccg-registration-0.8-alpha-1.tar.gz',
    'https://ccg-django-extras.googlecode.com/files/ccg-introspect-0.1.2.tar.gz',
    'https://ccg-django-extras.googlecode.com/files/ccg-makoloader-0.2.6.tar.gz',
    'https://bitbucket.org/ccgmurdoch/ccg-django-extras/downloads/ccg-extras-0.1.7.tar.gz',
    'https://ccg-django-extras.googlecode.com/files/ccg-auth-0.3.3.tar.gz',
    'https://yaphc.googlecode.com/files/yaphc-0.1.5.tgz',
    'https://github.com/downloads/muccg/djamboloader/djamboloader-0.1.2.tar.gz',
]

importlib_available = True
try:
    import importlib
except ImportError:
    # This will likely to happen before Python 2.7
    importlib_available = False

if not importlib_available:
    install_requires.append('importlib>=1.0.1,<1.1.0')

setup(name='yabiadmin',
      version='7.1.7',
      description='Yabi Admin',
      long_description='Yabi front end and administration web interface',
      author='Centre for Comparative Genomics',
      author_email='yabi@ccg.murdoch.edu.au',
      packages=packages,
      package_data={
          '': ["%s/%s" % (dirglob, fileglob)
              for dirglob in (["."] + ['/'.join(['*'] * num) for num in range(1, 15)])                         # yui is deeply nested
              for fileglob in ['*.mako', '*.html', '*.css', '*.js', '*.png', '*.jpg', 'favicon.ico', '*.gif', 'mime.types', '*.wsgi', '*.svg']]
      },
      zip_safe=False,
      install_requires=install_requires,
      dependency_links=dependency_links,
      extras_require={
          'tests': tests_require,
          'dev': dev_requires,
          'postgresql': postgresql_requires,
          'mysql': mysql_requires,
      })
