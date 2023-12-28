from flask import current_app


class Message:
    def __init__(self, subject='', sender=None, to=None, cc=None, bcc=None, body=None, html=None, date=None, charset='utf-8', attachments=None, extra_headers=None):
        sender = sender or current_app.extensions['mail'].default_sender
        self.subject = subject
        self.sender = sender
        self.to = to or []
        self.cc = cc or []
        self.bcc = bcc or []
        self.body = body
        self.html = html
        self.date = date
        self.messageID = make_msgid()
        self.charset = charset
        self.attachments = attachments or []
        self.extra_headers = extra_headers or {}

    def _plaintext(self):
        text_part = MIMEText(self.body, _subtype='plain', _charset=self.charset)
        if not self.html:
            return text_part
        msg = MIMEMultipart('alternative')
        html_part = MIMEText(self.html, _subtype='html', _charset=self.charset)
        msg.attach(text_part)
        msg.attach(html_part)
        return msg

    def _format_recipients(self, recipients):
        if isinstance(recipients, str):
            recipients = [recipients]
        return ', '.join(list(set([formataddr(parseaddr(addr)) for addr in recipients])))

    def _attach_files(self, msg):
        for filename in self.attachments:
            if not os.path.isfile(filename):
                continue
            basename = os.path.basename(filename)

            ctype, encoding = mimetypes.guess_type(filename)
            if ctype is None or encoding is not None:
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)

            if maintype == 'text':
                with open(filename) as fp:
                    part = MIMEText(fp.read(), _subtype=subtype)
            elif maintype == 'image':
                with open(filename, 'rb') as fp:
                    part = MIMEImage(fp.read(), _subtype=subtype)
            elif maintype == 'audio':
                with open(filename, 'rb') as fp:
                    part = MIMEAudio(fp.read(), _subtype=subtype)
            else:
                with open(filename, 'rb') as fp:
                    part = MIMEBase(maintype, subtype)
                    part.set_payload(fp.read())
                encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=basename)
            msg.attach(part)

    def _message(self):
        if self.attachments:
            msg = MIMEMultipart()
            msg.attach(self._plaintext())
        else:
            msg = self._plaintext()

        msg['Subject'] = Header(self.subject, self.charset).encode()
        msg['From'] = formataddr(parseaddr(self.sender))
        msg['Date'] = formatdate(self.date, localtime=True)
        msg['Message-ID'] = self.messageID

        if self.to:
            msg['To'] = self._format_recipients(self.to)

        if self.cc:
            msg['Cc'] = self._format_recipients(self.cc)

        if self.bcc:
            msg['Bcc'] = self._format_recipients(self.bcc)

        if self.attachments:
            self._attach_files(msg)

        if self.extra_headers:
            for k, v in self.extra_headers.items():
                msg[k] = Header(v, self.charset).encode()
        return msg

    def as_string(self):
        return self._message().as_string()

    def send(self, connection):
        connection.send(self)
