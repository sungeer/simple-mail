import os
import smtplib
import mimetypes

from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, formataddr, make_msgid, parseaddr

from flask import current_app


class _MailMixin:
    def send(self, message):
        with self.connect() as connection:
            message.send(connection)

    def connect(self):
        app = getattr(self, 'app', None) or current_app
        try:
            return Connection(app.extensions['mail'])
        except KeyError:
            raise RuntimeError('the curent application was not configured with mail')


class _Mail(_MailMixin):
    def __init__(self, server, username, password, port, use_tls, use_ssl, default_sender, debug):
        self.server = server
        self.username = username
        self.password = password
        self.port = port
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.default_sender = default_sender
        self.debug = debug


class Mail(_MailMixin):
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.state = self.init_app(app)
        else:
            self.state = None

    def init_mail(self, config, debug=False):
        return _Mail(
            config.get('MAIL_SERVER', '127.0.0.1'),
            config.get('MAIL_USERNAME'),
            config.get('MAIL_PASSWORD'),
            config.get('MAIL_PORT', 25),
            config.get('MAIL_USE_TLS', False),
            config.get('MAIL_USE_SSL', False),
            config.get('MAIL_DEFAULT_SENDER'),
            int(config.get('MAIL_DEBUG', debug))
        )

    def init_app(self, app):
        state = self.init_mail(app.config, app.debug)
        app.extensions['mail'] = state
        return state

    def __getattr__(self, name):
        return getattr(self.state, name, None)
