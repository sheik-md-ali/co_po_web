from flask import Flask, render_template, request, redirect, url_for, flash, session, Blueprint
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sys
sys.path.append('D:/co_po_web')
from website.models import User, Admin
from io import BytesIO
from PIL import Image
import base64
from website import db

auth = Blueprint('auth', __name__)

def authenticate_user(email, password):
    admin_user = Admin.query.filter_by(email=email).first()
    if admin_user and admin_user.check_password(password):
        return admin_user, 'admin'
    else:
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return user, 'user'
    return None, None

@auth.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user, user_type = authenticate_user(email, password)

        if user:
            login_user(user)
            session['user_type'] = user_type

            if user_type == 'admin':
                return redirect(url_for('admin_routes.admin_dashboard'))
            else:
                return redirect(url_for('user_routes.user_dashboard'))
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.login'))  # Redirect back to the login page on login failure
    else:
        # GET request, render the login page
        return render_template('login.html')

@auth.route('/back-to-dashboard')
@login_required
def back_to_dashboard():
    if current_user.is_authenticated:
        if session.get('user_type') == 'admin':
            return redirect(url_for('admin_routes.admin_dashboard'))
        else:
            return redirect(url_for('user_routes.user_dashboard'))
    else:
        return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_type', None)
    return redirect(url_for('views.index'))

# Route to render the registration form
@auth.route('/register', methods=['GET'])
def show_register_form():
    return render_template('register.html')

@auth.route('/register', methods=['POST'])
def register():
    # Retrieve form data
    name = request.form['name']
    mobile_no = request.form['mobile_no']
    email = request.form['email']
    college = request.form['college']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    profile_photo = request.files['profile_photo']

    # Check if passwords match
    if password != confirm_password:
        flash('Passwords do not match', 'error')
        return redirect(url_for('views.index'))

    # Check if a user with the same email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('User with this email already exists', 'error')
        return redirect(url_for('views.index'))

    # Resize and save the profile photo
    if profile_photo:
        img = Image.open(profile_photo)
        img.thumbnail((300, 300))  # Adjust the size as needed
        output_buffer = BytesIO()
        img.save(output_buffer, format='JPEG')
        resized_image_data = output_buffer.getvalue()

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Create a new User instance
    new_user = User(
        name=name,
        mobile_no=mobile_no,
        email=email,
        college=college,
        profile_photo=resized_image_data,  # Save the resized image data
        password=hashed_password,
        is_approved=False  # Set is_approved to True
    )

    # Commit the new user to the database
    db.session.add(new_user)
    db.session.commit()

    flash('Registration request submitted for approval!', 'success')
    return redirect(url_for('auth.login'))
