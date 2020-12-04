from flask import flash

def flash_form_errors(form):
    for error in form.errors:
        if error == "confirm": continue
        flash(error.capitalize() + ': ' + ''.join(form.errors[error]))

def resend_after_to_seconds(resend_after):
    times, time_unit = resend_after.split()
    secs = 0

    if   time_unit == "MINS":
        secs = int(times) * 60
    elif time_unit == "HOUR" or time_unit == "HOURS":
        secs = int(times) * 60 * 60

    return secs

def seconds_to_resend_after(secs):
    mins = int(secs / 60)

    if mins < 60:
        resend_after = str(mins) + " MINS"
    else:
        hrs = int(mins / 60)
        if hrs == 1:
            resend_after = str(hrs) + " HOUR"
        else:
            resend_after = str(hrs) + " HOURS"

    return resend_after
