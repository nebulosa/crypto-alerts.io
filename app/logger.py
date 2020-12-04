import logging, requests, smtplib

from config import Config

class MailgunLogger(logging.Handler):
    def emit(self, record): #record.message is the log message
        payload = {
            "from":    Config.APP_FROM,
            "to":      Config.APP_ADMIN,
            "subject": "{} critical error".format(Config.APP_DOMAIN),
            "text":    self.format(record)
        }

        response = requests.post(
                       Config.MAILGUN_DOMAIN,
                       verify=False,
                       auth=("api", Config.MAILGUN_API),
                       data=payload,
                   )

        if response.status_code != requests.codes.ok:
            raise ValueError("Error while mailing above exception, mailgun api response: {}, {}"
                             .format(response.status_code, response.text))

class SMTPLogger(logging.Handler):
    def send_email_smtp(self, subject, recipients, text_body, html_body):
        smtpserver = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)

        if Config.SMTP_USE_TLS == "yes":
            smtpserver.ehlo()
            smtpserver.starttls()
            smtpserver.ehlo() # extra characters to permit edit

        smtpserver.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)

        from email.mime.multipart import MIMEMultipart
        from email.mime.text      import MIMEText

        #create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = Config.APP_FROM
        msg['To']      = recipients

        text_body = MIMEText(text_body, 'plain')
        html_body = MIMEText(html_body, 'html')

        #attach parts into message container.
        #according to RFC 2046, the last part of a multipart message, in this case
        #the HTML message, is best and preferred.
        msg.attach(text_body)
        msg.attach(html_body)

        smtpserver.sendmail(Config.APP_FROM, recipients, msg.as_string())
        smtpserver.quit()

    def emit(self, record): #record.message is the log message
        subject = "{} critical error".format(Config.APP_DOMAIN)
        self.send_email_smtp(subject, Config.APP_ADMIN, self.format(record), self.format(record))
