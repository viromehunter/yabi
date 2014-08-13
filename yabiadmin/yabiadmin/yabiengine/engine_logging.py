import os
import logging
from functools import partial

# Use the create_TYPE_logger methods to create loggers that add context to all
# messages logged with that logger.
#
# Ex:
#
# logger = logging.getLogger(__name__) # Usually defined at top of module
#
# task_logger.create_task_logger(logger, 100)
# task_logger.info("Stagein started.")
#
# The "Stageing started" LogRecord will be associated with Task 100.
#
# YabiDBHandler is configured in settings.py to log all the LogRecords with
# context to the yabiadmin.yabiengine.models.Syslog


logger = logging.getLogger(__name__)


def create_logger(context_type, logger, pk):
    return logging.LoggerAdapter(logger, {
        'yabi_context': {
            'type': context_type,
            'id': pk}})


create_workflow_logger = partial(create_logger, 'workflow')
create_job_logger = partial(create_logger, 'job')
create_task_logger = partial(create_logger, 'task')


class YabiDBHandler(logging.Handler):

    def emit(self, record):
        from yabiadmin.yabiengine import models as m
        if hasattr(record, 'yabi_context'):
            table_name = record.yabi_context.get('type')
            table_id = record.yabi_context.get('id')
            try:
                m.Syslog.objects.create(
                    message=self.format_message(record),
                    table_name=table_name,
                    table_id=table_id)
            except:
                logger.exception("Couldn't log to Syslog table")
                logger.error("Original message %s", self.format_message(record))

    def format_message(self, record):
        msg = record.getMessage()
        if record.exc_info is not None:
            formatter = logging.Formatter()
            traceback = formatter.formatException(record.exc_info)
            msg = msg.rstrip()
            msg = os.linesep.join((msg, traceback))

        return msg


class YabiContextFilter(logging.Filter):

    def filter(self, record):
        return hasattr(record, 'yabi_context')
