from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import os
import hashlib

db = SQLAlchemy()

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    skimlinks_id = db.Column(db.String(150), nullable=True)
    shorten_links = db.Column(db.Boolean, default=False)
    api_key = db.Column(db.String(150), unique=True, nullable=True)

# Generate API key for user
def generate_api_key():
    return hashlib.sha256(os.urandom(64)).hexdigest()
