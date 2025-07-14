import os
import dotenv

dotenv.load_dotenv()

class Config:
    UPLOAD_FOLDER = "static/uploads"
    TESTING = False

class DevelopmentConfig(Config):
    TEMPLATES_AUTO_RELOAD = True
