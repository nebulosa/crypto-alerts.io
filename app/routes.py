import time, zlib, base64, urllib, re, os, random

from flask       import render_template, flash, redirect, url_for, request
from flask       import send_from_directory
from flask_login import login_required, current_user, login_user, logout_user
from datetime    import datetime, timedelta
from mongoengine.queryset.visitor import Q

from app            import app, login_manager, scheduler
from app.mail       import send_confirmation_email, send_reset_passwd_email
from app.forms      import LoginForm, RegisterForm, EmailForm, PasswordForm
from app.forms      import PasswordRecoverForm, SettingsForm, AlertForm
from app.forms      import modal_authenticated_forms, modal_forms
from app.forms      import alert_forms
from app.token      import generate_status_token, confirm_email_token
from app.token      import confirm_status_token
from app.utils      import flash_form_errors
from app.utils      import resend_after_to_seconds, seconds_to_resend_after
from app.models     import User, Alert
from app.alerts     import alert_meets_price_criteria, alert_meets_max_emails_criteria
from app.alerts     import alert_trigger
from app.exchanges  import sync_binance_prices, sync_bitso_prices
from app.exchanges  import supported_currencies, supported_cryptocurrencies
from app.exchanges  import supported_currencies_dict, supported_cryptocurrencies_dict
from app.exchanges  import get_current_price
from app.decorators import user_anonymous_or_confirmed_required
from app.decorators import user_confirmed_required, user_mod_required
from app.decorators import user_admin_required

ALERTS_PER_PAGE = app.config['APP_ALERTS_PER_PAGE']

@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()

#http://flask.pocoo.org/docs/0.12/templating/#context-processors
@app.context_processor
def inject_global_template_variables():
    return dict(
        APP_URL   = app.config['APP_URL'],
        APP_TITLE = app.config['APP_TITLE'],
        APP_PARTICLES_BG_EFFECT = app.config['APP_PARTICLES_BG_EFFECT'],
        APP_MAX_ALERTS_PER_MONTH = app.config['APP_MAX_ALERTS_PER_MONTH'],
        APP_MAX_EMAIL_NOTIFICATIONS_PER_MONTH = app.config['APP_MAX_EMAIL_NOTIFICATIONS_PER_MONTH'],
        APP_MAX_ALERTS_SPAM_STRIKES = app.config['APP_MAX_ALERTS_SPAM_STRIKES'],
    )

#call a function within jinja2, https://stackoverflow.com/a/22966127/890858
@app.context_processor
def utility_processors():
    def supported_currencies_dict_jinja2():
        return supported_currencies_dict()

    def supported_cryptocurrencies_dict_jinja2():
        return supported_cryptocurrencies_dict()

    return dict(
        supported_currencies_dict_jinja2=supported_currencies_dict,
        supported_cryptocurrencies_dict_jinja2=supported_cryptocurrencies_dict,
    )

@app.route('/index')
@app.route('/index.html')
@app.route('/index.php')
def index_html():
    return redirect(url_for('index'))

@app.route('/')
@user_anonymous_or_confirmed_required
def index():
    user = None
    if current_user.is_authenticated:
        user = User.objects(email=current_user.email).first()

    return render_template("index.html.j2", forms=alert_forms(user=user))

@app.route('/login', methods=['POST'])
def login(referrer=None):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if request.method == 'POST' and form.validate():
        user = User.objects(email=form.email.data).first()
        if user is None:
            flash('Invalid Email or Password')
            return redirect(url_for('index'))
        else:
            if user.check_password(form.password.data):
                login_user(user)
                user.last_seen = datetime.utcnow()
                user.save()

                if not current_user.is_active:
                    flash("Disabled account")

                if referrer:
                    referrer = decode_uri(referrer)
                else:
                    referrer = request.referrer

                return redirect(referrer)
            else:
                flash('Invalid Email or Password')
                return redirect(url_for('index'))

    flash_form_errors(form)
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    if not app.config['APP_REGISTER']:
        return render_template('user_register_disabled.html.j2')

    form = RegisterForm()
    if request.method == 'POST' and form.validate():
        if User.objects(email=form.email.data).first() is None:
            if User.objects().first() is None:
                profile="ADMIN" #make 1st user ADMIN
            else:
                profile="USER"

            new_user = User(
                email=form.email.data,
                password=form.password.data,
                profile=profile,
            ).save()
            send_confirmation_email(new_user)
            login_user(new_user)
            return redirect(url_for('user_unconfirmed'))
        else:
            flash('Email already registered "{}"'.format(form.email.data))

    flash_form_errors(form)
    return redirect(url_for('index'))

@app.route('/user/unconfirmed')
def user_unconfirmed():
    if current_user.confirmed:
        flash('Account already confirmed "{}", continue to the login page'.format(current_user.email))
        return redirect('index')
    return render_template('user_unconfirmed.html.j2', forms=modal_authenticated_forms())

@app.route('/confirm/<item>/<token>')
def confirm(item, token):
    if   item == "email":
        return confirm_email(token)
    elif item == "state":
        return confirm_status(token)
    else:
        return render_template('404.html.j2'), 404

def confirm_email(token):
    email = confirm_email_token(token)
    if not email:
        flash('Invalid confirmation code or expired (> 1hr)')
        return redirect(url_for('index'))

    user = User.objects(email=email).first()
    if user.confirmed:
        flash('Account already confirmed "{}", continue to the login page'.format(email))
    else:
        user.confirmed    = True
        user.confirmed_on = datetime.now()
        user.save()
        flash('Account sucessfully confirmed: {}'.format(email))
    return redirect(url_for('index'))

def confirm_status(token):
    status = confirm_status_token(token)
    if not status:
        flash('Invalid confirmation code or expired (> 1hr)')
        return render_template('404.html.j2'), 404

    user = User.objects(email=status['email']).first()
    if user is None:
        flash("Account doesn't exists: {}".format(status['email']))
        return redirect(url_for('register'))
    elif user.status[-1]['state'] != status['state']:
        flash('Invalid confirmation code or expired (> 1hr)')
        return render_template('404.html.j2'), 404
    else:
        if user.status[-1]['acked']:
            flash('Already confirmed, a moderation will review your case shortly')
        else:
            user.status[-1]['acked'] = True
            user.save()

            moderator = user.status[-1]['modered_by']
            msg = ("¡Hey!, <a href='{}'>{}</a> confirmed of received ({}),"
                   " please take a moment to review the account profile"
                   " thank you for helping to improve <a href='{}'>{}</a>.")
            msg = msg.format(
                    url_for('profile', username=user.username), user.username,
                    status['state'],
                    app.config['APP_URL'], app.config['APP_URL'],
                  )
            moderator.notify(msg)

            msg = ("Thank you for confirm your new state ({}), shortly a moderator will review your case.")
            msg = msg.format(status['state'])
            user.notify(msg, email=True)
            flash(msg)

    return redirect(url_for('index'))

@app.route('/user/resend')
@login_required
def user_resend():
    send_confirmation_email(current_user)
    flash('A new confirmation code was sent to {}, please verify your email to continue'.format(current_user.email))
    return redirect(url_for('user_unconfirmed'))

@app.route('/user/recover', methods=['POST'])
def user_recover():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = PasswordRecoverForm()
    if request.method == 'POST' and form.validate():
        user = User.objects(email=form.email.data).first()
        if user is None:
            flash('A recover code was sent to {}, please verify your email to continue'.format(form.email.data))
            return redirect(url_for('index'))
        else:
            if user.is_confirmed:
                send_reset_passwd_email(user)
                flash('A recover code was sent to {}, please verify your email to continue'.format(form.email.data))
                return redirect(url_for('index'))
            else:
                flash('Unverified account "{}", please login and resent a verification code'.format(form.email.data))
                return redirect(url_for('index'))

    flash_form_errors(form)
    return redirect(url_for('index'))

@app.route('/user/reset/<token>')
def user_reset(token):
    email = confirm_email_token(token)
    if not email:
        flash('Invalid reset code or expired (> 1hr)')
        return redirect(url_for('index'))

    user = User.objects(email=email).first()
    login_user(user)

    flash('Account recovered, please set a new password')
    return render_template("index.html.j2", forms=modal_authenticated_forms(user=user), modal="account-edit-password")

@app.route('/user/reset', methods=['POST'])
@login_required
@user_confirmed_required
def user_reset_password():
    form = PasswordResetForm()
    if request.method == 'POST' and form.validate():
        user = User.objects(id=current_user.id).first()
        user.reset_password(form.password.data).save()
        flash('Your password has been restored successfully')
    return redirect(url_for('index'))

@app.route('/user/edit/password', methods=['POST'])
@login_required
@user_confirmed_required
def password_edit():
    form = PasswordForm()
    if request.method == 'POST' and form.validate():
        user = User.objects(id=current_user.id).first()
        user.reset_password(form.password.data).save()
        flash('Your password account has been updated sucessfully!')
        return redirect(url_for('index'))

    flash_form_errors(form)
    return redirect(url_for('index'))

@app.route('/user/settings/edit', methods=['POST'])
@login_required
@user_confirmed_required
def user_settings_edit():
    form = SettingsForm()
    if request.method == 'POST' and form.validate():
        user = User.objects(email=current_user.email).first()
        user.default_alert_method = form.method.data
        user.default_currency = form.currency.data
        user.default_exchange = form.exchange.data
        user.save()
        flash("Your new settings have been saved!")
        return redirect(url_for('index'))

    flash_form_errors(form)
    return redirect(url_for('index'))

@app.route('/user/delete')
@login_required
def user_delete():
    email = current_user.email
    user  = User.objects(email=email).first()

    user.notifications().delete()
    #TODO: mv alerts to a ghost account depending in how good theirs trades are
    user.alerts().delete()
    user.delete()

    logout_user()
    flash('Your account ({}) has been deleted successfully'.format(email))
    return redirect(url_for('index'))

@app.route('/alerts')
@login_required
@user_confirmed_required
def alerts():
    user = User.objects(email=current_user.email).first()
    return render_template('alerts.html.j2', forms=modal_authenticated_forms(user=user), user=user)

@app.route('/alert/add', methods=['POST'])
@login_required
@user_confirmed_required
def alert_add():
    form = AlertForm()
    if request.method == 'POST' and form.validate():
        user = User.objects(email=current_user.email).first()

        if not form.currency.data in supported_currencies(exchange=form.exchange.data):
            flash("{} doesn\\'t support {}".format(form.exchange.data, form.currency.data))
            return redirect(url_for('index'))

        if not form.cryptocurrency.data in supported_cryptocurrencies(exchange=form.exchange.data):
            flash("{} doesn\\'t support {}".format(form.exchange.data, form.cryptocurrency.data))
            return redirect(url_for('index'))

        alert = Alert(
            user=user,
            method=form.method.data,
            method_data=form.method_data.data,
            cryptocurrency=form.cryptocurrency.data,
            price_direction=form.price_direction.data,
            price=form.price.data,
            currency=form.currency.data,
            exchange=form.exchange.data,
            note=form.note.data,
            resend_after=resend_after_to_seconds(form.resend_after.data),
            notify_only_once=form.notify_only_once.data,
        )

        if alert_meets_price_criteria(alert):
            flash("{} price ${} {} is already {} ${} {} on {}, retry with new parameters".format(
                alert.cryptocurrency,
                get_current_price(alert.exchange, alert.currency, alert.cryptocurrency), alert.currency,
                alert.price_direction,
                alert.price, alert.currency,
                alert.exchange
            ))
            return redirect(url_for('index'))

        if not alert_meets_max_emails_criteria(alert):
            flash("Max amount of active alerts reached: {}".format(app.config['APP_MAX_ALERTS_PER_MONTH']))
            return redirect(url_for('terms_of_service'))

        alert.save()
        flash("Alert added successfully!")
        return redirect(url_for('alerts'))

    flash_form_errors(form)
    return redirect(url_for('index'))

@app.route('/alert/delete/<hash>')
@login_required
@user_confirmed_required
def alert_delete(hash):
    alert = Alert.objects(hash=hash).first()
    if not alert:
        flash("Such alert doesn' exists")
        return redirect(url_for('alerts'))

    alert.delete()
    flash('Alert deleted sucessfully')
    return redirect(url_for('alerts'))

@app.route('/alert/toggle/<hash>')
@login_required
@user_confirmed_required
def alert_toggle_state(hash):
    alert = Alert.objects(hash=hash).first()
    if not alert:
        flash("Such alert doesn' exists")
        return redirect(url_for('alerts'))

    if not alert.active and not alert_meets_max_emails_criteria(alert):
        flash("Max amount of active alerts reached: {}".format(app.config['APP_MAX_ALERTS_PER_MONTH']))
        return redirect(url_for('terms_of_service'))

    alert.active = not alert.active
    alert.save(clean=False)
    return redirect(url_for('alerts'))

@app.route('/alert/edit/<hash>', methods=['GET', 'POST'])
@login_required
@user_confirmed_required
def alert_edit(hash):
    alert = Alert.objects(hash=hash).first()
    if not alert:
        flash("Such alert doesn' exists")
        return redirect(url_for('alerts'))

    form = AlertForm()
    if request.method == 'POST' and form.validate():
        if not form.currency.data in supported_currencies(exchange=form.exchange.data):
            flash("{} doesn\\'t support {}".format(form.exchange.data, form.currency.data))
            return redirect(url_for('alert_edit', hash=hash))

        if not form.cryptocurrency.data in supported_cryptocurrencies(exchange=form.exchange.data):
            flash("{} doesn\\'t support {}".format(form.exchange.data, form.cryptocurrency.data))
            return redirect(url_for('alert_edit', hash=hash))

        alert.method           = form.method.data
        alert.method_data      = form.method_data.data
        alert.cryptocurrency   = form.cryptocurrency.data
        alert.price_direction  = form.price_direction.data
        alert.price            = form.price.data
        alert.currency         = form.currency.data
        alert.exchange         = form.exchange.data
        alert.note             = form.note.data
        alert.resend_after     = resend_after_to_seconds(form.resend_after.data)
        alert.notify_only_once = form.notify_only_once.data

        if alert_meets_price_criteria(alert):
            flash("{} price ${} {} is already {} ${} {} on {}, retry with new parameters".format(
                alert.cryptocurrency,
                get_current_price(alert.exchange, alert.currency, alert.cryptocurrency), alert.currency,
                alert.price_direction,
                alert.price, alert.currency,
                alert.exchange
            ))
            return redirect(url_for('alert_edit', hash=hash))

        alert.save()
        flash('Changes saved!')
        return redirect(url_for('alerts'))

    forms = alert_forms()
    forms['alert'].method.data = alert.method
    forms['alert'].method_data.data = alert.method_data
    forms['alert'].cryptocurrency.data = alert.cryptocurrency
    forms['alert'].price_direction.data = alert.price_direction
    forms['alert'].price.data = alert.price
    forms['alert'].currency.data = alert.currency
    forms['alert'].exchange.data = alert.exchange
    forms['alert'].note.data = alert.note
    forms['alert'].resend_after.data = seconds_to_resend_after(alert.resend_after)
    forms['alert'].notify_only_once.data = alert.notify_only_once

    return render_template("alert.edit.html.j2", forms=forms, hash=hash)

@app.route('/alert/report/<hash>')
def alert_report(hash):
    alert = Alert.objects(hash=hash).first()
    if not alert:
        flash("Such alert doesn' exists")
        return redirect(url_for('index'))

    alert.active = False
    alert.user.spam_strikes += 1
    if alert.user.spam_strikes == app.config['APP_MAX_ALERTS_SPAM_STRIKES']:
        alert.user.suspend()
    alert.save()
    flash("The reported alert has been disabled and the infractor notified, sorry for the inconvience!")
    return redirect(url_for('index'))

@app.route('/email/edit', methods=['POST'])
@login_required
@user_confirmed_required
def email_edit():
    form = EmailForm()
    if request.method == 'POST' and form.validate():
        if User.objects(email=form.email.data).first() is None:
            user = User.objects(email=current_user.email).first()
            user.email = form.email.data
            user.confirmed = False
            user.save()
            send_confirmation_email(user)
            flash("Your email has been updated, please confirm the new email address")
            return redirect(url_for('user_unconfirmed'))
        else:
            flash('Email already registered "{}"'.format(form.email.data))

    flash_form_errors(form)
    return redirect(url_for('index'))

@app.route('/notifications')
@login_required
@user_confirmed_required
def notifications():
    flash("Notifications!")
    return redirect(url_for('index'))

@app.route('/terms-of-service')
def terms_of_service():
    user = None
    if current_user.is_authenticated:
        user = User.objects(email=current_user.email).first()
    return render_template('terms_of_service.html.j2', forms=modal_authenticated_forms(user=user))

@app.route('/area-51/mods')
@login_required
def user_not_mod():
    return render_template('user_not_mod.html.j2')

@app.route('/area-51/admins')
@login_required
def user_not_admin():
    return render_template('user_not_admin.html.j2')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/img'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/exception')
@login_required
def error():
    raise Exception("I'm sorry, Dave. I'm afraid I can't do that.")

#############################################################################
############################## Scheduler Tasks ##############################
#############################################################################
# @scheduler.task('interval', seconds=3, misfire_grace_time=900)
@scheduler.task('interval', seconds=60, misfire_grace_time=900)
def ticker_exchange_prices():
    app.logger.debug("Getting Exchange Prices ...")
    sync_binance_prices()
    sync_bitso_prices()

@scheduler.task('interval', seconds=45, misfire_grace_time=900)
def ticker_alerts():
    with app.app_context():
        app.logger.debug("Processing Alerts ...")
        for alert in Alert.objects(active=True):
            app.logger.debug("Processing Alert: {}".format(alert.id))
            if alert_meets_price_criteria(alert):
                alert_trigger(alert)

#############################################################################
############################# 4xx / 5xx Errors ##############################
#############################################################################

@app.errorhandler(401)
def not_found_error(error):
    return render_template('401.html.j2', forms=modal_forms()), 401

@app.errorhandler(404)
def not_found_error(error):
    app.logger.debug(error)
    return render_template('404.html.j2', forms=modal_forms()), 404

@app.errorhandler(405)
def not_found_error(error):
    return render_template('405.html.j2', forms=modal_forms()), 405

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html.j2', forms=modal_forms()), 500
