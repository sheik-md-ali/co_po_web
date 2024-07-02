# user_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash
import sys
sys.path.append('D:/co_po_web')
from website.models import User, Subject, Assessment, AssessmentInstance, IAComponent
from io import BytesIO
from PIL import Image
import base64
from website import db

user_routes = Blueprint('user_routes', __name__)

@user_routes.route('/user/dashboard')
@login_required
def user_dashboard():
    return render_template('user/user_dashboard.html')


@user_routes.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # Retrieve form data
    name = request.form['name']
    mobile_no = request.form.get('mobile_no')  # Make mobile_no optional

    # Retrieve the current user
    current_user.name = name
    current_user.mobile_no = mobile_no  # Update mobile_no if provided

    # Commit changes to the database
    db.session.commit()

    flash('Profile updated successfully!', 'success')
    return redirect(url_for('user_routes.user_dashboard'))



@user_routes.route('/user_subjects')
@login_required
def user_subjects():
    # Retrieve subjects for the current user by querying the database
    user_subjects = Subject.query.filter_by(user_id=current_user.id).all()

    return render_template('user/user_subjects.html', user_subjects=user_subjects)


@user_routes.route('/upload_assessment')
def upload_assessment():
    # Assuming current_user contains the logged-in user object
    user_id = current_user.id

    # Query subjects associated with the logged-in user
    subjects = Subject.query.filter_by(user_id=user_id).all()

    # Query the unit test count for each assessment
    assessments = Assessment.query.all()

    # Initialize the set for included units 
    included_units = set()

    return render_template('user/upload_assessment.html', subjects=subjects, assessments=assessments, included_units=included_units)


@user_routes.route('/user/mapping_for_assessment')
@login_required
def mapping_for_assessment():
    return render_template('user/mapping_for_assessment.html')