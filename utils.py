from flask_mail import Mail, Message, Attachment
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_executor import Executor

mail = Mail()
executor = Executor()
limiter = Limiter(
    get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

@executor.job
def send_email(recipient, subject, body):
    msg = Message(f"{subject}", recipients=[f'{recipient}'])
    msg.body = f"{body}"
    mail.send(msg)