from flask import render_template, request, redirect, url_for, flash,session
from app import app
from models import db, User, Category, Product, Cart, Transaction, Order
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime


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
def admin_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session and User.query.get(session['user_id']).is_admin:
            return func(*args, **kwargs)
        if not 'user_id' in session:
            flash('You must be logged in first')
            return redirect(url_for('login'))
        else:
            flash('You must be an admin to access this page')
            return redirect(url_for('index'))
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
    user = User.query.get(session['user_id'])
    if user.is_admin:
        return redirect(url_for('admin'))

    return render_template('index.html')

@app.route('/logout')
@auth_required  # decorator for authentication required before accessing this route 
def logout():
    session.pop('user_id', None)
    flash('You have logged out')
    return redirect(url_for('login'))

#---------Admin routes---------!

@app.route('/admin')
@admin_required
def admin():
    categories = Category.query.all()
    return render_template('admin.html', categories = categories)

@app.route('/category/show/<int:id>')
@admin_required
def show_category(id):
    category = Category.query.get(id)
    if not category:
        flash('Category does not exist')
        return redirect(url_for('admin'))
    return render_template('/product/show.html', category = category)

@app.route('/category/delete/<int:id>', methods = ['POST','GET'])
@admin_required
def delete_category(id):
    if request.method == 'POST':
        category = Category.query.get(id)
        if not category:
            flash("Category doesn't exist")
            return redirect(url_for('admin'))
        db.session.delete(category)
        db.session.commit()

        flash("Category deleted successfully")
        return redirect(url_for('admin'))
    else:

        category = Category.query.get(id)
        return render_template('/category/delete.html', category = category)
    
@app.route('/category/edit/<int:id>', methods = ['GET','POST'])
@admin_required
def edit_category(id):
    if request.method == 'POST':
        updated_name = request.form.get('name')
        category = Category.query.get(id)
        if not category:
            flash('Category does not exist')
            return redirect(url_for('admin'))
        category.name = updated_name
        db.session.commit()
        flash('Category updated successfully')
        return redirect(url_for('admin'))
    if request.method == 'GET':
        category = Category.query.get(id)
        if not category:
            flash('Category does not exist')
            return redirect(url_for('admin'))
        return render_template('category/edit.html', category = category)

@app.route('/category/add')
@admin_required
def add_category():
    return render_template('/category/add.html')

@app.route('/category/add' , methods = ['POST'])
@admin_required
def add_category_post():
    name = request.form.get('name')
    if not name:
        flash('Please enter category name')
        return redirect(url_for('add_category'))
    category = Category(name = name)
    db.session.add(category)
    db.session.commit()
    flash('Category added successfully')
    return redirect(url_for('admin'))


#------Products--------------#
@app.route('/product/add/<int:category_id>', methods = ['GET', 'POST'])
@admin_required
def add_product(category_id):
    if request.method == 'GET':
        category = Category.query.get(category_id)
        if not category:
            flash('Category does not exist')
            return redirect(url_for('admin'))
        return render_template('product/add.html', category = category)
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        quantity = request.form.get('quantity')
        man_date = request.form.get('man_date')
        if not name or not price or not quantity or not man_date:
            flash('Please enter all details')
            return redirect(url_for('add_product', category_id = category_id))
        try:
            price= int(price)
            quantity = int(quantity)
            man_date = datetime.strptime(man_date, '%Y-%m-%d')
        except ValueError:
            flash('Price and Quantity should be numbers')
            return redirect(url_for('add_product', category_id = category_id))
        category = Category.query.get(category_id)
        if price<0 or quantity<0:
            flash('Price and Quantity should be positive')
            return redirect(url_for('add_product', category_id = category_id))
        if man_date > datetime.now():
            flash('Manufacturing date should be less than current date')
            return redirect(url_for('add_product', category_id = category_id))
        product = Product(name = name, price = price, quantity = quantity, man_date = man_date, category_id = category_id)
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully')
        return redirect(url_for('show_category', id = category_id))
