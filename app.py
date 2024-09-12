from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import User, generate_api_key
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
import urllib.parse

app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route
@app.route('/')
def home():
    return redirect(url_for('login'))

# Register user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password, api_key=generate_api_key())
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('register.html')

# Login user
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))

    return render_template('login.html')

# User dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

# Rewrite and shorten link
@app.route('/rewrite-link', methods=['POST'])
@login_required
def rewrite_link():
    product_url = request.json.get('product_url')

    if not product_url:
        return jsonify({"error": "Product URL is required"}), 400

    # Rewrite link with Skimlinks Publisher ID
    encoded_url = urllib.parse.quote(product_url, safe='')
    affiliate_url = f"https://go.skimresources.com?id={current_user.skimlinks_id}&xs=1&url={encoded_url}"

    # Shorten link if the user has that option enabled
    if current_user.shorten_links:
        affiliate_url = shorten_isgd_url(affiliate_url)

    return jsonify({"affiliate_url": affiliate_url}), 200

# Shorten URL using is.gd
def shorten_isgd_url(long_url):
    api_url = f"https://is.gd/create.php?format=simple&url={long_url}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.text.strip()
    return long_url

# Generate OpenAPI spec for users
@app.route('/openapi/<user_id>')
@login_required
def openapi_spec(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "User API",
            "description": "API for Skimlinks affiliate link generation.",
            "version": "1.0.0"
        },
        "paths": {
            "/rewrite-link": {
                "post": {
                    "summary": "Rewrite and shorten affiliate link",
                    "parameters": [
                        {
                            "name": "Authorization",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Bearer API key"
                        }
                    ],
                    "responses": {
                        "200": {"description": "Affiliate link rewritten"}
                    }
                }
            }
        }
    }
    return jsonify(openapi_spec)

# Account settings page
@app.route('/account', methods=['GET', 'POST'])
@login_required
def account_settings():
    if request.method == 'POST':
        skimlinks_id = request.form.get('skimlinks_id')
        shorten_links = 'shorten_links' in request.form

        # Update user details
        current_user.skimlinks_id = skimlinks_id
        current_user.shorten_links = shorten_links
        db.session.commit()
        
        return redirect(url_for('dashboard'))

    return render_template('account.html', user=current_user)

if __name__ == '__main__':
    app.run(debug=True)
