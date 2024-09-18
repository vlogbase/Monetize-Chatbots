from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    publisher_id = db.Column(db.String(50), default='44501')
    site_id = db.Column(db.String(50))
    custom_id = db.Column(db.String(50))
    api_key = db.Column(db.String(100))
