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

@user_routes.route('/register', methods=['GET'])
def show_register_form():
    return render_template('register.html')

@user_routes.route('/register', methods=['POST'])
def register():
    # Retrieve form data
    name = request.form['name']
    mobile_no = request.form.get('mobile_no')  # Make mobile_no optional
    email = request.form['email']
    college = request.form['college']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    # Check if passwords match
    if password != confirm_password:
        flash('Passwords do not match', 'error')
        return redirect(url_for('index'))

    # Check if a user with the same email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('User with this email already exists', 'error')
        return redirect(url_for('index'))

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Create a new User instance
    new_user = User(
        name=name,
        mobile_no=mobile_no,  # Set mobile_no to the provided value or None
        email=email,
        college=college,
        password=hashed_password,
        is_approved=False
    )

    # Commit the new user to the database
    db.session.add(new_user)
    db.session.commit()

    flash('Registration request submitted for approval!', 'success')
    return redirect(url_for('index'))

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


@user_routes.route('/register_subject', methods=['GET'])
@login_required
def show_subject_registration_form():
    return render_template('user/register_subject.html')

@user_routes.route('/register_subject', methods=['GET', 'POST'])
@login_required
def register_subject():
    if request.method == 'POST':
        # Retrieve form data
        faculty_name = request.form['faculty_name']
        branch = request.form['branch']
        year = request.form['year']
        semester = request.form['semester']
        regulation = request.form['regulation']
        academic_year = request.form['academic_year']
        course = request.form['course']
        course_code = request.form['course_code']
        section = request.form['section']
        integrated = request.form['integrated']  # Retrieve integrated option

        # Create a new Subject instance associated with the current user
        new_subject = Subject(
            faculty_name=faculty_name,
            branch=branch,
            year=year,
            semester=semester,
            regulation=regulation,
            academic_year=academic_year,
            course=course,
            course_code=course_code,
            section=section,
            integrated=integrated,  # Add integrated option to the Subject instance
            user=current_user
        )

        # Commit the new subject to the database
        db.session.add(new_subject)
        db.session.commit()

        flash('Subject registration successful!', 'success')
        return redirect(url_for('user_routes.user_dashboard'))
    else:
        return render_template('user/register_subject.html')




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


def generate_instance_name(assessment_name, count):
    if count == 1:
        return assessment_name
    else:
        return f"{assessment_name} {count}"
    
@user_routes.route('/user/assessment_modification')
@login_required
def assessment_modification():
    user_id = current_user.id
    # Query subjects associated with the logged-in user
    subjects = Subject.query.filter_by(user_id=user_id).all()
    assessments = AssessmentInstance.query.filter_by(user_id=user_id).all()
    return render_template('user/assignment_modification.html', assessments=assessments, subjects=subjects)


@user_routes.route('/user/add_assessment', methods=['POST'])
@login_required
def add_assessment():
    assessment_type = request.form['assessment_type']
    count = int(request.form['count'])
    max_marks = int(request.form['max_marks'])
    subject_code = request.form['subjectCode']  # Retrieve subject code from form

    # Retrieve subject based on subject code
    subject = Subject.query.filter_by(course_code=subject_code).first()

    if not subject:
        flash('Subject not found.', 'error')
        return redirect(url_for('user_routes.add_assessment'))

    # Create assessment name based on assessment type and max marks
    if assessment_type == 'OTHER':
        name = f"{request.form['other_assessment_name'].upper()}({max_marks}M)"
    else:
        name = f"{assessment_type}({max_marks}M)"

    # Check if an assessment with the same name, max marks, and subject exists
    existing_assessment = Assessment.query.filter_by(
        name=name,
        max_marks=max_marks,
        subject_id=subject.id,
        user_id=current_user.id
    ).first()

    if existing_assessment:
        # If assessment exists, increment count
        existing_assessment.count += count
        db.session.commit()
        flash('Assessment count incremented successfully.', 'success')
    else:
        # Otherwise, create new assessment
        new_assessment = Assessment(name=name, count=count, max_marks=max_marks, subject=subject, user=current_user)
        db.session.add(new_assessment)
        db.session.commit()
        flash('New assessment added successfully.', 'success')

        # Generate and add assessment instances
        existing_instance_count = AssessmentInstance.query.filter_by(assessment_id=new_assessment.id).count()
        for i in range(1, count + 1):
            instance_name = f"{name} {existing_instance_count + i}"  # Generate instance name
            new_instance = AssessmentInstance(
                name=instance_name,
                assessment=new_assessment,
                user=current_user,
                subject=subject
            )
            db.session.add(new_instance)
        db.session.commit()

    return redirect(url_for('user_routes.assessment_modification'))


@user_routes.route('/user/modify_assessment', methods=['POST'])
@login_required
def modify_assessment():
    action = request.form['action']
    assessment_id = int(request.form['assessment_id'])
    assessment = Assessment.query.filter_by(id=assessment_id, user_id=current_user.id).first_or_404()
    
    if action == 'delete_assessment':
        # Delete all instances associated with the assessment
        AssessmentInstance.query.filter_by(assessment_id=assessment.id).delete()
        db.session.delete(assessment)
        db.session.commit()
        flash('Assessment deleted successfully.', 'success')
    elif action == 'decrement_count':
        if assessment.count > 0:
            # Decrement count and delete the last instance
            assessment.count -= 1
            instance_to_delete = AssessmentInstance.query.filter_by(assessment_id=assessment.id).order_by(AssessmentInstance.id.desc()).first()
            if instance_to_delete:
                db.session.delete(instance_to_delete)
                db.session.commit()
                flash('Count decremented successfully.', 'success')
        else:
            flash('Count cannot be decremented further.', 'error')
    elif action == 'increment_count':
        # Increment count and create a new instance
        assessment.count += 1
        new_instance_name = f"{assessment.name} {assessment.count}"  # Generate instance name
        new_instance = AssessmentInstance(
            name=new_instance_name,
            assessment=assessment,
            user=current_user,
            subject=assessment.subject  # Assign the subject object to the new instance
        )
        db.session.add(new_instance)
        db.session.commit()
        flash('Count incremented successfully.', 'success')


    return redirect(url_for('user_routes.assessment_modification'))


@user_routes.route('/get_assessment_instances')
def get_assessment_instances():
    user_id = current_user.id  # Assuming current_user contains the logged-in user object
    subject_id = request.args.get('subjectId')
    
    instances = AssessmentInstance.query.filter_by(user_id=user_id, subject_id=subject_id).all()
    
    instance_data = [{'id': instance.id, 'name': instance.name} for instance in instances]
    
    return jsonify(instance_data)

@user_routes.route('/course_plan')
@login_required
def course_plan():
    # Assuming current_user contains the logged-in user object
    user_id = current_user.id
    
    # Query subjects associated with the logged-in user
    subjects = Subject.query.filter_by(user_id=user_id).all()

    return render_template('user/course_plan.html', subjects=subjects)


@user_routes.route('/add_ia', methods=['POST'])
@login_required
def add_ia():
    # Assuming current_user contains the logged-in user object
    user_id = current_user.id

    # Extract data from the request form
    subject_code = request.form.get('subjectCode')
    ia_name = request.form.get('iaName')
    assessment_instances = request.form.getlist('assessmentInstance')


    # Optionally, you can return a response to the client, such as a success message or redirect
    return redirect(url_for('user_routes.course_plan'))
