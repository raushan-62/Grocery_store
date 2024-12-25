from flask import render_template, request, redirect, url_for, flash,session
from app import app
from models import db, User, Category, Product, Cart, Transaction, Order
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login',methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username = username).first()

    if not user or not check_password_hash(user.passhash, password):
        flash("Invalid username or password")
        return redirect(url_for('login'))
    session['user_id'] = user.id
    flash('You have successfully logged in')
    return redirect(url_for('index'))
@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register',methods = ['POST'])
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    name = request.form.get('name')

    if not username or not password or not confirm_password or not name:
        flash("All fields are required")
        return redirect(url_for('register'))
    
    if password != confirm_password:
        flash("Password don't match")
        return redirect(url_for('register'))
    
    user = User.query.filter_by(username = username).first()
    if user:
        flash("Username already exists")
        return redirect(url_for('register'))
    
    password_hash = generate_password_hash(password)
    user = User(username = username, passhash = password_hash, name = name)
    db.session.add(user)
    db.session.commit()

    return redirect(url_for('login'))

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash('You must be logged in first')
            return redirect(url_for('login'))
    return inner


@app.route('/profile')
@auth_required  # decorator for authentication required before accessing this route 
def profile():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('profile.html', user = user)
    else:
        flash('You must be logged in first')
        return redirect(url_for('login'))

@app.route('/profile', methods = ['POST'])
@auth_required
def profile_post():
    username = request.form.get('username')
    password = request.form.get('password')
    new_password = request.form.get('new_password')
    name = request.form.get('name')
    if not username or not password or not new_password:
        flash('Please enter all details')
        return redirect(url_for('profile'))
    user = User.query.get(session['user_id'])
    if not check_password_hash(user.passhash, password):
        flash('Incorrect Password')
        return redirect(url_for('profile'))
    if username != user.username:
        new_username = User.query.filter_by(username = username).first()
        if new_username:
            flash('Username already exists')
            return redirect(url_for('profile'))
    new_password_hash = generate_password_hash(new_password)
    user.username = username
    user.passhash = new_password_hash
    if name:
        user.name = name
    user.name = user.name
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('profile'))
@app.route('/')
@auth_required
def index():

    return render_template('index.html')

@app.route('/logout')
@auth_required  # decorator for authentication required before accessing this route 
def logout():
    session.pop('user_id', None)
    flash('You have logged out')
    return redirect(url_for('login'))
