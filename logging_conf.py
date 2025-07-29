import logging
import os
from config import Config
from flask_mail import Mail, Message
from utils import executor
from flask import has_request_context, request


class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None

        return super().format(record)
    

class SematextFormatter(RequestFormatter):
    def format(self, record):
        message = super().format(record)
        return f"{os.environ['SEMATEXT_PASSWORD']}:[{message}]"
    

class SMTPErrorHandler(logging.Handler):
    def emit(self, record):
        try:
            mail = Mail()
            msg = Message(subject=record.levelname,
                          recipients=[Config.MAIL_USERNAME],
                          body=self.format(record))
            executor.submit(mail.send, msg)
        except Exception as e:
            logging.error(f"Failed to send email: {e}")


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "smtp": {
            "()": RequestFormatter,
            "format": "[%(asctime)s] %(remote_addr)s requested %(url)s\n%(levelname)s in %(module)s: %(message)s",
        },
        "sematext": {
            "()": SematextFormatter,
            "format": "[%(asctime)s] %(remote_addr)s requested %(url)s\n%(levelname)s in %(module)s: %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default"
        },
        "smtp_handler": {
            "class": "logging_conf.SMTPErrorHandler",
            "level": "ERROR",
            "formatter": "smtp",
        },
        "sematext_handler": {
            "class": "logging.handlers.SysLogHandler",
            "address": ('logsene-syslog-receiver.eu.sematext.com', 514),
            "level": "INFO",
            "formatter": "sematext"
        }
    },
    "loggers": {
        "app": {
            "level": "DEBUG",
            "handlers": ["smtp_handler", "sematext_handler"],
            "propagate": False
        }
    },
    "root": {
        "level": "WARNING",
        "handlers": ["console"]
    }
}