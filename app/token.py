from itsdangerous import URLSafeSerializer, URLSafeTimedSerializer

from config import Config

def generate_email_token(email):
    serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
    return serializer.dumps(email, salt='email-confirm')

def confirm_email_token(token, expiration=3600): #1 hour
    serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
    try:
        email  = serializer.loads(token, salt='email-confirm', max_age=expiration)
    except:
        return False
    return email

def generate_status_token(email, state):
    serializer = URLSafeSerializer(Config.SECRET_KEY)
    status = {'email': email, 'state': state}
    return serializer.dumps(status, salt='status-confirm')

def confirm_status_token(token):
    serializer = URLSafeSerializer(Config.SECRET_KEY)
    try:
        status = serializer.loads(token, salt='status-confirm')
    except:
        return False
    return status
