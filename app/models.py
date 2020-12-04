from flask       import request
from hashlib     import md5
from datetime    import datetime
from flask_login import current_user

from app         import app, db, bcrypt
from app.mail    import send_notification_email

import app.constants as constants

class User(db.Document):
    email    = db.StringField(required=True, unique=True)
    password = db.StringField(required=True); password_hashed = db.BooleanField(default=False)
    profile  = db.StringField(required=True, default=constants.USER_PROFILES[0])
    phone    = db.StringField(required=False)

    status   = db.ListField(db.DictField(), required=True, default=[{
                    'state'      : constants.USER_STATES[0],
                    'modered_by' : None, # db.ReferenceField('User')
                    'date'       : datetime.now(),
                    'acked'      : False,
                }])

    spam_strikes = db.IntField(required=True, default=0)

    #can be calculated from the status array but saved here for performance
    silenced_times  = db.IntField(required=True, default=0)
    suspended_times = db.IntField(required=True, default=0)

    confirmed     = db.BooleanField(default=False)
    confirmed_on  = db.DateTimeField()
    registered_on = db.DateTimeField(default=datetime.now())
    last_seen     = db.DateTimeField(default=datetime.now())

    #default user settings
    default_alert_method = db.StringField(required=True, default=constants.ALERT_METHODS[0])
    default_currency = db.StringField(required=True, default=constants.CURRENCIES[0])
    default_exchange = db.StringField(required=True, default=constants.EXCHANGES[0])

    def clean(self):
        #clean will be called on .save()
        #you can do whatever you want to clean data before saving

        #workaround for already hashed password, mongoengine makes difficult to
        #override the __init__ constructor:
        #https://stackoverflow.com/questions/16881624/mongoengine-0-8-0-breaks-my-custom-setter-property-in-models
        #http://docs.mongoengine.org/guide/document-instances.html#pre-save-data-validation-and-cleaning
        if not self.password_hashed:
            self.password        = bcrypt.generate_password_hash(self.password).decode('utf-8')
            self.password_hashed = True

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def reset_password(self, password):
        self.password        = bcrypt.generate_password_hash(password).decode('utf-8')
        self.password_hashed = True
        return self

    def avatar(self, size):
        return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % (md5(self.email.encode('utf-8')).hexdigest(), size)

    def set_status(self, state):
        if state in constants.USER_STATES:
            status = {
                'state'      : state,
                #TODO 09-08-2018 19:04 >> how to save by ObjectId?
                'modered_by' : current_user.to_dbref(),
                'date'       : datetime.now(),
                'acked'      : False,
            }

            self.status.append(status)

            if   self.is_silenced():
                self.silenced_times  += 1
            elif self.is_suspended():
                self.suspended_times += 1

        self.save()

        return self

    def is_silenced(self):
        if self.status[-1]['state'] == "SILENCED":
            return True
        else:
            return False

    def silence(self):
        self.set_status("SILENCED")

    def unsilence(self):
        self.set_status("ACTIVE")

    def is_suspended(self):
        if self.status[-1]['state'] == "SUSPENDED":
            return True
        else:
            return False

    def suspend(self):
        self.set_status("SUSPENDED")

    def unsuspend(self):
        self.set_status("ACTIVE")

    def is_admin(self):
        if self.profile == "ADMIN":
            return True
        else:
            return False

    def is_mod(self):
        if self.profile == "MOD" or self.profile == "ADMIN":
            return True
        else:
            return False

    def member_since(self):
        day   = self.confirmed_on.day
        month = self.confirmed_on.month
        year  = self.confirmed_on.year

        return '%s %d %d' % (month, day, year)

    def last_seen_since(self):
        mins  = self.last_seen.minute
        hour  = self.last_seen.hour

        day   = self.last_seen.day
        month = self.last_seen.month
        year  = self.last_seen.year

        return '%d %s %d, %s:%s' % (day, month, year, hour, mins)

    def alerts(self):
        return Alert.objects(user=self).order_by('-date')

    def notifications(self):
        return Notification.objects(user=self).order_by('-date')

    def notify(self, msg):
        if msg is None:
            return False
        else:
            new_notification = Notification(
                user=self,
                msg=msg,
                ).save()
            send_notification_email(new_notification)
            return True

    @property
    def is_confirmed(self):
        return self.confirmed

    def __repr__(self):
        return '<User %r>' % (self.email)

    #required for flask-login
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        if self.status[-1]['state'] == "ACTIVE":
            return True
        else:
            return False

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
    #finish flask-login requirements

    meta = {
        'strict': True,
    }


class Notification(db.Document):
    user     = db.ReferenceField('User', required=True)
    msg      = db.StringField(required=True)
    date     = db.DateTimeField(default=datetime.now())
    seen     = db.BooleanField(default=False)

    hash     = db.StringField(required=True, unique=True)

    def clean(self):
        hash = self.user.id    + \
               str(self.msg)   + \
               str(self.date)  + \
               str(self.seen)

        self.hash = md5(hash.encode('utf-8')).hexdigest()

    def __repr__(self):
        return '<Notification %r>' % (self.id)

class Alert(db.Document):
    user              = db.ReferenceField('User',       required=True)
    active            = db.BooleanField(required=True,  default=True)
    date              = db.DateTimeField(required=True, default=datetime.now())
    method            = db.StringField(required=True)
    method_data       = db.StringField(required=True)
    cryptocurrency    = db.StringField(required=True,   default="BTC")
    price_direction   = db.StringField(required=True,   choices=constants.PRICE_DIRECTIONS)
    price             = db.FloatField(required=True,    default=0.0)
    currency          = db.StringField(required=True,   choices=constants.CURRENCIES)
    exchange          = db.StringField(required=True,   choices=constants.EXCHANGES)
    note              = db.StringField()
    resend_after      = db.IntField(required=True,      default=21600) #6hrs
    notify_only_once  = db.BooleanField(required=True,  default=True)
    notify_times      = db.IntField(required=True,      default=0)
    notify_date       = db.DateTimeField(required=False)
    hash              = db.StringField(required=True,   unique=True)

    def clean(self):
        hash = self.user.email           + \
               str(self.date)            + \
               str(self.method)          + \
               str(self.method_data)     + \
               str(self.cryptocurrency)  + \
               str(self.price_direction) + \
               str(self.price)           + \
               str(self.currency)        + \
               str(self.exchange)        + \
               str(self.note)            + \
               str(self.resend_after)    + \
               str(self.notify_only_once)

        self.date = datetime.now()
        self.hash = md5(hash.encode('utf-8')).hexdigest()

    def __repr__(self):
        return '<Alert %r>' % (self.id)

class Price(db.Document):
    exchange       = db.StringField(required=True)
    currency       = db.StringField(required=True)
    cryptocurrency = db.StringField(required=True)
    current_price  = db.FloatField(required=True)
    date           = db.DateTimeField(default=datetime.now())

    def cryptocurrencies(self):
        return Price.objects().distinct(field="cryptocurrency")

    def clean(self):
        self.date = datetime.now()

    def __repr__(self):
        return '<Price %r>' % (self.id)
