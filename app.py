from flask import Flask, render_template, redirect, url_for, request, session, send_file
from flask import Response
from models import db, User
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env
import urllib.parse
import uuid
import yaml
import io
import os

# Initialize the Flask app
app = Flask(__name__)

# Use environment variables for sensitive information
app.secret_key = os.environ.get('SECRET_KEY', 'your_default_secret_key')  # Replace 'your_default_secret_key' for production
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')  # Replace with your production database URI

# Initialize SQLAlchemy with Flask app
db.init_app(app)

# Create tables if they do not exist
@app.before_first_request
def create_tables():
    db.create_all()

# Homepage route
@app.route('/')
def index():
    return render_template('index.html')

# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(email=email).first():
            return 'Email already registered.'
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return 'Invalid credentials.'
    return render_template('login.html')

# User logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Dashboard route where users can manage their settings
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        user.publisher_id = request.form['publisher_id'] or '44501'
        user.site_id = request.form['site_id']
        user.custom_id = request.form['custom_id']
        user.api_key = str(uuid.uuid4())  # Generate a new API key using UUID
        db.session.commit()
    return render_template('dashboard.html', user=user)

# API endpoint to convert URLs into affiliate links
@app.route('/api/convert', methods=['POST'])
def api_convert():
    api_key = request.headers.get('Authorization').split(" ")[1] if request.headers.get('Authorization') else None
    if not api_key:
        return {'error': 'Unauthorized'}, 401
    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return {'error': 'Unauthorized'}, 401
    data = request.get_json()
    original_url = data.get('url')
    if not original_url:
        return {'error': 'URL is required'}, 400
    encoded_url = urllib.parse.quote(original_url, safe='')
    params = {
        'id': user.publisher_id,
        'xs': '1',
        'url': encoded_url
    }
    if user.site_id:
        params['id'] += f"X{user.site_id}"
    if user.custom_id:
        params['xcust'] = user.custom_id
    affiliate_url = f"https://go.skimresources.com?{urllib.parse.urlencode(params)}"
    return {'affiliate_url': affiliate_url}

# Route to generate the OpenAPI specification
@app.route('/generate_openapi')
def generate_openapi():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    with open('openapi_template.yaml', 'r') as f:
        spec = yaml.safe_load(f)
    spec['info']['title'] = 'Monetize Chatbots API'
    spec['servers'][0]['url'] = request.url_root.rstrip('/')
    spec['paths']['/api/convert']['post']['security'][0]['api_key'] = []
    yaml_spec = yaml.dump(spec)
    return Response(yaml_spec, mimetype='application/x-yaml')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
