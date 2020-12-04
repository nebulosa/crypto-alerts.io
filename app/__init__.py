from flask             import Flask
from flask_login       import LoginManager
from flask_bcrypt      import Bcrypt
from flask_mongoengine import MongoEngine
from flask_apscheduler import APScheduler

from config            import Config
from app.logger        import SMTPLogger, MailgunLogger

import logging, sys

app = Flask(__name__)
app.config.from_object(Config)
app.logger.setLevel(logging.DEBUG)

db = MongoEngine()
db.init_app(app)

bcrypt = Bcrypt()
bcrypt.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

#output to stdout so docker can keep track of it
stdout_logger = logging.StreamHandler(sys.stdout)
stdout_logger.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
stdout_logger.setLevel(logging.DEBUG)
app.logger.addHandler(stdout_logger)

mail_logger = None

if Config.APP_MAIL_PROVIDER == "SMTP":
    mail_logger = SMTPLogger()
else:
    mail_logger = MailgunLogger()

mail_logger.setLevel(logging.ERROR)
mail_logger.setFormatter(logging.Formatter('''
    Message type:       %(levelname)s
    Location:           %(pathname)s:%(lineno)d
    Module:             %(module)s
    Function:           %(funcName)s
    Time:               %(asctime)s

    Message:

    %(message)s
'''))
app.logger.addHandler(mail_logger)

from app import routes
