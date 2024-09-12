import os

# Basic Flask config
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")

# Database config
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///users.db")  # Replace with Azure DB URI
SQLALCHEMY_TRACK_MODIFICATIONS = False
