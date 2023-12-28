
class Connection:
    def __init__(self, mail):
        self.mail = mail

    def __enter__(self):
        self.host = self.configure_host()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if self.host:
            self.host.quit()

    def configure_host(self):
        if self.mail.use_ssl:
            host = smtplib.SMTP_SSL(self.mail.server, self.mail.port)
        else:
            host = smtplib.SMTP(self.mail.server, self.mail.port)
        host.set_debuglevel(int(self.mail.debug))
        if self.mail.use_tls:
            host.starttls()
        if self.mail.username and self.mail.password:
            host.login(self.mail.username, self.mail.password)
        return host

    def extract_recipients(self, msg):
        recipients = []
        for field in ('To', 'Cc', 'Bcc'):
            if msg[field]:
                recipients.extend(msg[field].split(', '))
        return set(recipients)

    def send(self, msg):
        if isinstance(msg, Message):
            msg = msg.message()
        recipients = self.extract_recipients(msg)
        sender = msg['From']
        if self.host:
            self.host.sendmail(sender, list(recipients), msg.as_string())
