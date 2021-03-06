#/usr/bin/env python

from setuptools import setup, find_packages

exec(compile(open('yabishell/version.py').read(), 'yabishell/version.py', 'exec'))

setup(name='yabish',
     version = __version__,
     description = 'Command line interface for YABI.',
     author = 'Tamas Szabo',
     author_email = 'tszabo AT ccg.murdoch.edu.au',
     url = 'http://ccg.murdoch.edu.au',
     packages = find_packages(),

     package_data = {
        '': ['help/*'],
     },
     entry_points = { 'console_scripts': [ 'yabish = yabishell.yabish:main' ] },
)
