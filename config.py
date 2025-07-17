class Config:
    UPLOAD_FOLDER = "static/uploads"
    TESTING = False
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USERNAME = "socialsage.management@gmail.com"
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_DEFAULT_SENDER = ("Social Sage Management", "socialsage.management@gmail.com")

class DevelopmentConfig(Config):
    TEMPLATES_AUTO_RELOAD = True
