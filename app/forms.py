from flask_wtf import FlaskForm, RecaptchaField
from wtforms   import StringField, FloatField
from wtforms   import PasswordField, BooleanField, SubmitField
from wtforms   import SelectField
from wtforms.validators import InputRequired, Email, Length, EqualTo

from app.exchanges import supported_cryptocurrencies

import app.constants as constants

def modal_unauthenticated_forms():
    return {
        'login':    LoginForm(),
        'register': RegisterForm(),
        'recover':  PasswordRecoverForm(),
        'email':    EmailForm(),
        'password': PasswordForm(),
    }

def modal_authenticated_forms(user=None):
    if user:
        return {
            **modal_unauthenticated_forms(),
            'settings': SettingsForm(
                method=user.default_alert_method,
                currency=user.default_currency,
                exchange=user.default_exchange,
            )
        }

    else:
        return {
            **modal_unauthenticated_forms(),
            'settings': SettingsForm(),
        }

def modal_forms():
    return {
        **modal_authenticated_forms()
    }

def alert_forms(user=None):
    if user:
        if user.default_alert_method == "EMAIL":
            user_method_data = user.email
        else:
            user_method_data = user.phone
    else:
        return {
            **modal_authenticated_forms(),
            'alert': AlertForm(),
        }

    return {
        **modal_authenticated_forms(user=user),
        'alert': AlertForm(
            method=user.default_alert_method,
            method_data=user_method_data,
            currency=user.default_currency,
            exchange=user.default_exchange,
        ),
    }

class LoginForm(FlaskForm):
    email    = StringField('Email',
               render_kw={"placeholder": "Email"},
               validators=[
                   InputRequired(),
                   Email(),
               ])

    password = PasswordField('Password',
               render_kw={"placeholder": "Password"},
               validators=[InputRequired()])

    submit   = SubmitField('Login')

class RegisterForm(FlaskForm):
    email    = StringField('Email',
               render_kw={"placeholder": "Email"},
               validators=[
                   InputRequired(),
                   Email(),
                   Length(max=128),
               ])

    password = PasswordField('Password',
               render_kw={"placeholder": "Password"},
               validators=[
                   InputRequired(),
                   Length(min=4, max=1024),
                   EqualTo('confirm'),
               ])

    confirm  = PasswordField('Confirm Password',
               render_kw={"placeholder": "Confirm Password"},
               validators=[
                   InputRequired(),
                   Length(min=4, max=1024),
             ])

    captcha  = RecaptchaField()

    submit   = SubmitField('Register')

class EmailForm(FlaskForm):
    email = StringField('New Email',
               render_kw={"placeholder": "New Email"},
               validators=[
                   InputRequired(),
                   Email(),
                   EqualTo('confirm'),
               ])
    confirm  = StringField('Confirm New Email',
               render_kw={"placeholder": "Confirm New Email"},
               validators=[
                   InputRequired(),
                   Email(),
               ])
    submit   = SubmitField('Change Email')

class PasswordRecoverForm(FlaskForm):
    email    = StringField('Email',
               render_kw={"placeholder": "Email"},
               validators=[
                   InputRequired(),
                   Email(),
                   Length(max=128),
               ])

    captcha  = RecaptchaField()

    submit   = SubmitField('Recover Account')

class PasswordForm(FlaskForm):
    password = PasswordField('New Password',
               render_kw={"placeholder": "New Password"},
               validators=[
                   InputRequired(),
                   Length(min=4, max=1024),
                   EqualTo('confirm'),
               ])

    confirm  = PasswordField('Confirm New Password',
               render_kw={"placeholder": "Confirm New Password"},
               validators=[
                   InputRequired(),
                   Length(min=4, max=1024),
               ])

    submit   = SubmitField('Change Password')

class SettingsForm(FlaskForm):
    method_choices = [(alert_method, alert_method) for alert_method in constants.ALERT_METHODS]
    method = SelectField("Alert",
           choices=method_choices,
           validators=[
              InputRequired(),
           ])

    currency_choices = [(currency, currency) for currency in constants.CURRENCIES]
    currency = SelectField("Currency",
                     choices=currency_choices,
                     validators=[
                        InputRequired(),
                     ])

    exchange_choices = [(exchange, exchange) for exchange in constants.EXCHANGES]
    exchange = SelectField("Exchange",
               choices=exchange_choices,
               validators=[
                    InputRequired(),
               ])

    submit   = SubmitField('Save Changes')

class AlertForm(FlaskForm):
    method_choices = [(alert_method, alert_method) for alert_method in constants.ALERT_METHODS]
    method = SelectField("Alert",
           choices=method_choices,
           validators=[
              InputRequired(),
           ])

    method_data = StringField('Alert Data',
                  default="m@to.tld",
                  validators=[
                      InputRequired(),
                      Email(),
                      Length(max=128),
                  ])

    cryptocurrency_choices = supported_cryptocurrencies()
    if  cryptocurrency_choices:
        cryptocurrency_choices = [(cryptocurrency, cryptocurrency) for cryptocurrency in cryptocurrency_choices]
    else:
        cryptocurrency_choices = [(cryptocurrency, cryptocurrency) for cryptocurrency in constants.CRYPTOCURRENCIES]

    cryptocurrency = SelectField("Cryptocurrency",
                     render_kw={"style": "max-width:100%;"},
                     choices=cryptocurrency_choices,
                     default="BTC",
                     validators=[
                        InputRequired(),
                     ])

    price_direction_choices = [(price_direction, price_direction) for price_direction in constants.PRICE_DIRECTIONS]
    price_direction = SelectField("Price Direction",
                      choices=price_direction_choices,
                      validators=[
                        InputRequired(),
                      ])

    price = FloatField('Price',
            render_kw={"placeholder": "0.00", "autofocus": True},
            validators=[
                InputRequired(),
            ])

    currency_choices = [(currency, currency) for currency in constants.CURRENCIES]
    currency = SelectField("Currency",
               choices=currency_choices,
               validators=[
                    InputRequired(),
               ])

    exchange_choices = [(exchange, exchange) for exchange in constants.EXCHANGES]
    exchange = SelectField("Exchange",
               choices=exchange_choices,
               validators=[
                    InputRequired(),
               ])

    note = StringField('Note',
           render_kw={"placeholder": "This will appear alongside the alert to help give you context (optional)"},
           validators=[
                Length(max=256),
           ])

    resend_after_choices = [(time, time) for time in constants.RESEND_TIMES]
    resend_after = SelectField("Resend After",
               choices=resend_after_choices,
               default=constants.RESEND_TIMES[(len(constants.RESEND_TIMES)//2)+2],
               validators=[
                    InputRequired(),
               ])

    notify_only_once = BooleanField('Notify only once', default=True)

    submit = SubmitField('Set Alert')
