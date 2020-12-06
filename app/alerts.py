from flask         import flash
from datetime      import datetime

from app           import app
from app.mail      import send_alert_email
from app.models    import Alert
from app.exchanges import get_current_price

def alert_meets_price_criteria(alert):
    current_price = get_current_price(alert.exchange, alert.currency, alert.cryptocurrency)

    if alert.price_direction == "ABOVE" and alert.price < current_price:
        return alert_meets_criteria_times(alert)
    if alert.price_direction == "BELOW" and alert.price > current_price:
        return alert_meets_criteria_times(alert)

    return False

def alert_meets_max_emails_criteria(alert):
    if len(Alert.objects(user=alert.user, active=True)) >= app.config['APP_MAX_ALERTS_PER_MONTH']:
        if not alert.user.is_mod():
            return False

    return True

def alert_meets_criteria_times(alert):
    if alert.notify_only_once and alert.notify_times == 0:
        return True
    if not alert.notify_only_once:
        seconds_since_last_notification = (datetime.now()-alert.notify_date).total_seconds()
        # app.logger.debug("{} secs since last time".format(seconds_since_last_notification))
        # app.logger.debug("{} secs resend after".format(alert.resend_after))
        if seconds_since_last_notification > alert.resend_after:
            return True
    return False

def alert_trigger(alert):
    if alert.user.emails_this_month() >= app.config['APP_MAX_EMAIL_NOTIFICATIONS_PER_MONTH']:
        return

    alert.notify_date   = datetime.now()
    alert.notify_times += 1
    alert.user.emails_this_month(add=1)
    alert.save()
    send_alert_email(alert)
