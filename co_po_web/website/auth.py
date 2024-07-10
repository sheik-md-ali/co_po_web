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

