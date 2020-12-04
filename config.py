import os
import urllib.parse

class Config(object):
    #general settings
    APP_DOMAIN = os.environ.get('APP_DOMAIN', 'domain.tdl')
    APP_ADMIN  = os.environ.get('APP_ADMIN',  'admin@'+APP_DOMAIN)
    APP_FROM   = os.environ.get('APP_FROM',   'no-reply@' + APP_DOMAIN)
    APP_URL    = os.environ.get('APP_URL',    'https://'  + APP_DOMAIN)
    APP_TITLE  = os.environ.get('APP_TITLE',   APP_DOMAIN)

    APP_ALERTS_PER_PAGE = int(os.environ.get('APP_ALERTS_PER_PAGE', 20))

    APP_REGISTER = os.environ.get('APP_REGISTER', True)
    APP_REGISTER = False if APP_REGISTER == "no" else True

    APP_PARTICLES_BG_EFFECT = os.environ.get('APP_PARTICLES_BG_EFFECT', True)
    APP_PARTICLES_BG_EFFECT = False if APP_PARTICLES_BG_EFFECT == "no" else True

    #flask-wtf
    SECRET_KEY = os.environ.get('SECRET_KEY', 'you-will-never-guess')

    #flask-mongoengine
    MONGODB_HOST     = os.environ.get('MONGODB_HOST',         'mongodb')
    MONGODB_TCP_PORT = int(os.environ.get('MONGODB_TCP_PORT', 27017))
    MONGODB_DB       = os.environ.get('MONGODB_DB',           'app')
    MONGODB_USER     = os.environ.get('MONGODB_USER',         'app')
    MONGODB_PASSWD   = os.environ.get('MONGODB_PASSWD',       'app')

    MONGODB_USER     = urllib.parse.quote_plus(MONGODB_USER)
    MONGODB_PASSWD   = urllib.parse.quote_plus(MONGODB_PASSWD)

    MONGODB_SETTINGS = {
        'db':       MONGODB_DB,
        'host':     MONGODB_HOST,
        'port':     MONGODB_TCP_PORT,
        'username': MONGODB_USER,
        'password': MONGODB_PASSWD,
    }

    APP_MAIL_PROVIDER = os.environ.get('APP_MAIL_PROVIDER', 'SMTP')

    SMTP_SERVER    = os.environ.get('SMTP_SERVER',   'localhost')
    SMTP_PORT      = int(os.environ.get('SMTP_PORT',  25))
    SMTP_USERNAME  = os.environ.get('SMTP_USERNAME', 'guest')
    SMTP_PASSWORD  = os.environ.get('SMTP_PASSWORD', 'you-will-never-guess')
    SMTP_USE_TLS   = os.environ.get('SMTP_USE_TLS',  'yes')

    MAILGUN_API    = os.environ.get('MAILGUN_API',   'you-will-never-guess')
    MAILGUN_DOMAIN = os.environ.get('MAILGUN_DOMAIN', APP_DOMAIN)

    #recaptcha
    RECAPTCHA_PUBLIC_KEY  = os.environ.get('RECAPTCHA_PUBLIC_KEY',  'you-will-never-guess')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', 'you-will-never-guess')

    #app limits
    APP_MAX_ALERTS_PER_MONTH = int(os.environ.get('APP_MAX_ALERTS_PER_MONTH', 100))
    APP_MAX_EMAIL_NOTIFICATIONS_PER_MONTH = int(os.environ.get('APP_MAX_EMAIL_NOTIFICATIONS_PER_MONTH', 100))
    APP_MAX_ALERTS_SPAM_STRIKES = int(os.environ.get('APP_MAX_ALERTS_SPAM_STRIKES', 3))

    #costly cpu/bandwith usage
    APP_HIT_EXCHANGE_APIS_EVERY_SECONDS    = 60
    APP_VERIFY_GLOBAL_ALERTS_EVERY_SECONDS = 60

    #enable/disable email sending
    APP_MAIL_SENDING = os.environ.get('APP_MAIL_SENDING', True)
    APP_MAIL_SENDING = False if APP_MAIL_SENDING == "no" else True

    #apscheduler
    SCHEDULER_API_ENABLED       = True
    SCHEDULER_API_PREFIX        = "/scheduler"
    JSONIFY_PRETTYPRINT_REGULAR = False #https://github.com/pallets/flask/issues/2549

    #per environment settings
    APP_ENVIRONMENT = os.environ.get('APP_ENVIRONMENT', 'development')

    if   APP_ENVIRONMENT == 'development':
        DEBUG   = True
        TESTING = True #disable recaptcha
        os.environ['TZ'] = 'America/Mexico_City' #required for scheduler
    elif APP_ENVIRONMENT == 'production' :
        DEBUG  = False
        SCHEDULER_API_ENABLED = False
        os.environ['TZ'] = 'America/Mexico_City' #required for scheduler
