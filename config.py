import os
class Config:
    UPLOAD_FOLDER = "static/uploads"
    TESTING = False
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USERNAME = "socialsage.management@gmail.com"
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_DEFAULT_SENDER = ("Social Sage Management", "socialsage.management@gmail.com")
    GOOGLE_CLIENT_ID = "134250277130-fgcjv8quafib87o3sj9ild7pr6om4p1o.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_DISCOVERY_URL = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )


class DevelopmentConfig(Config):
    TEMPLATES_AUTO_RELOAD = True
