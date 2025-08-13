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
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    EXECUTOR_TYPE = "thread"
    EXECUTOR_MAX_WORKERS = 5
    MAX_FORM_MEMORY_SIZE = 1 * 1024 * 1024  # 1 MB
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB


class DevelopmentConfig(Config):
    TEMPLATES_AUTO_RELOAD = True
