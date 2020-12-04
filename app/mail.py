from app       import app
from flask     import render_template, url_for
from app.token import generate_email_token
from app.decorators import threaded

import requests, smtplib

APP_FROM = app.config['APP_FROM']
APP_URL  = app.config['APP_URL']

@threaded
def send_email(subject, recipients, text_body, html_body):
    with app.app_context():
        if not app.config['APP_MAIL_SENDING']:
            app.logger.debug('Email sending is disabled!, set the APP_MAIL_SENDING variable to enable it')
            app.logger.debug('Fake mail out')
            app.logger.debug('from: {}'.format(APP_FROM))
            app.logger.debug('to: {}'.format(recipients))
            app.logger.debug('subject: {}'.format(subject))
            app.logger.debug('text: {}'.format(text_body))
            app.logger.debug('html: {}'.format(html_body))
            return

        if app.config['APP_MAIL_PROVIDER'] == "SMTP":
            send_email_smtp(subject, recipients, text_body, html_body)
        else:
            send_email_mailgun(subject, recipients, text_body, html_body)

def send_email_smtp(subject, recipients, text_body, html_body):
    SMTP_SERVER   = app.config['SMTP_SERVER']
    SMTP_PORT     = app.config['SMTP_PORT']
    SMTP_USERNAME = app.config['SMTP_USERNAME']
    SMTP_PASSWORD = app.config['SMTP_PASSWORD']
    SMTP_USE_TLS  = app.config['SMTP_USE_TLS']

    smtpserver    = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

    if SMTP_USE_TLS == "yes":
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.ehlo() # extra characters to permit edit

    smtpserver.login(SMTP_USERNAME, SMTP_PASSWORD)

    from email.mime.multipart import MIMEMultipart
    from email.mime.text      import MIMEText

    #create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = APP_FROM
    msg['To']      = recipients

    text_body = MIMEText(text_body, 'plain')
    html_body = MIMEText(html_body, 'html')

    #attach parts into message container.
    #according to RFC 2046, the last part of a multipart message, in this case
    #the HTML message, is best and preferred.
    msg.attach(text_body)
    msg.attach(html_body)

    smtpserver.sendmail(APP_FROM, recipients, msg.as_string())
    smtpserver.quit()
    app.logger.debug('SUCCESS: Message: "{}", to: "{}"'.format(subject, recipients))

def send_email_mailgun(subject, recipients, text_body, html_body):
    MAILGUN_API    = app.config['MAILGUN_API']
    MAILGUN_DOMAIN = app.config['MAILGUN_DOMAIN']

    uri     = 'https://api.mailgun.net/v3/{}/messages'.format(MAILGUN_DOMAIN)
    payload = {
        'from':    APP_FROM,
        'to':      recipients,
        'subject': subject,
        'text':    text_body,
        'html':    html_body,
    }

    response = requests.post(
        uri,
        verify=False,
        auth=('api', MAILGUN_API),
        data=payload,
    )

    if response.status_code == requests.codes.ok:
        app.logger.debug('SUCCESS: Message: "{}", to: "{}"'.format(subject, recipients))
        app.logger.debug(response.json())
    else:
        app.logger.debug('ERROR: Message: "{}", to: "{}", status: "{}"'.
                         format(subject, recipients, response.status_code))
        app.logger.debug(response.json())

def send_confirmation_email(user):
    token = generate_email_token(user.email)
    confirm_email_url = url_for('confirm', item="email", token=token, _external=True)
    app.logger.debug('Confirm url: {}'.format(confirm_email_url))

    send_email("Email confirmation: {}".format(APP_URL),
               user.email,
               render_template("confirm_email.txt.j2",  user=user, confirm_url=confirm_email_url),
               render_template("confirm_email.html.j2", user=user, confirm_url=confirm_email_url))

def send_reset_passwd_email(user):
    token = generate_email_token(user.email)
    reset_password_url = url_for('user_reset', token=token, _external=True)
    app.logger.debug('Reset password url: {}'.format(reset_password_url))

    send_email("Email recovery procedure: {}".format(APP_URL),
               user.email,
               render_template("reset_password_email.txt.j2",  user=user, confirm_url=reset_password_url),
               render_template("reset_password_email.html.j2", user=user, confirm_url=reset_password_url))

def send_notification_email(notification):
    send_email("New Notification: {}".format(APP_URL),
               notification.user.email,
               render_template("notification_email.txt.j2",  notification=notification),
               render_template("notification_email.html.j2", notification=notification))

def send_alert_email(alert):
    send_email("New Alert: {}".format(APP_URL),
               alert.user.email,
               render_template("alert.email.txt.j2",  alert=alert),
               render_template("alert.email.html.j2", alert=alert))
