import os

from optparse import make_option

from lettuce import Runner

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Runs lettuce features'

    option_list = BaseCommand.option_list[1:] + (
        make_option('--app-name',
                    action='store',
                    dest='app_name',
                    default='yabi',
                    help='Application name'),

        make_option('--with-xunit',
                    action='store_true',
                    dest='enable_xunit',
                    default=False,
                    help='Output JUnit XML test results to a file'),

        make_option('--xunit-file',
                    action='store',
                    dest='xunit_file',
                    default=None,
                    help='Write JUnit XML to this file. Defaults to lettucetests.xml'),
    )

    def handle(self, *args, **options):
        app_name = options.get('app_name')
        if app_name:
            module = __import__(app_name)
            path = '%s/yabifeapp/features/' % os.path.dirname(module.__file__)
            print "Feature path = %s" % path
            runner = Runner(path, verbosity=options.get('verbosity'),
                            enable_xunit=options.get('enable_xunit'),
                            xunit_filename=options.get('xunit_file'),)

            runner.run()
        else:
            raise CommandError('Application name not provided')
