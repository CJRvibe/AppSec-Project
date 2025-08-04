from flask_mail import Mail, Message, Attachment
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_executor import Executor
from authlib.integrations.flask_client import OAuth
from config import Config
import os

mail = Mail()
executor = Executor()
limiter = Limiter(
    get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    meta_limits=["4/hour", "7/day"],
    storage_uri="memory://",
)

@executor.job
def send_email(recipient, subject, body):
    msg = Message(f"{subject}", recipients=[f'{recipient}'])
    msg.body = f"{body}"
    mail.send(msg)


oauth = OAuth()
google = oauth.register(
    name='google',
    client_id=Config.GOOGLE_CLIENT_ID,
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)