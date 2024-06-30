from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required
from werkzeug.security import generate_password_hash
import sys
sys.path.append('D:/co_po_web')
from website.models import User, Assessment, College, CollegeStaff, SubjectList, Subject, AssessmentInstance
from io import BytesIO
from PIL import Image
import base64
from website import db
from werkzeug.utils import secure_filename
import os
import pandas as pd

admin_routes = Blueprint('admin_routes', __name__)


@admin_routes.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if session.get('user_type') == 'admin':
        return render_template('admin/admin_dashboard.html')
    else:
        flash('Unauthorized access', 'error')
        return redirect(url_for('views.index'))

@admin_routes.route('/admin/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if session.get('user_type') == 'admin':
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            mobile_no = request.form['mobile_no']
            college = request.form['college']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            
            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return redirect(url_for('admin_routes.add_user'))
            
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('User with this email already exists', 'error')
                return redirect(url_for('admin_routes.add_user'))

            # Handle profile photo upload and resizing
            if 'profile_photo' in request.files:
                file = request.files['profile_photo']
                if file.filename != '':
                    image_data = file.read()
                    
                    # Resize the image
                    img = Image.open(BytesIO(image_data))
                    img.thumbnail((300, 300))  # Adjust the size as needed
                    output_buffer = BytesIO()
                    img.save(output_buffer, format='JPEG')
                    resized_image_data = output_buffer.getvalue()
                    
                    # Save the resized image data to the database
                    new_user = User(
                        name=name, 
                        email=email, 
                        mobile_no=mobile_no, 
                        college=college, 
                        profile_photo=resized_image_data, 
                        password=generate_password_hash(password),
                        is_approved=True  # Set is_approved to True
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    
                    flash('User added successfully', 'success')
                    return redirect(url_for('admin_routes.add_user'))
                else:
                    flash('No profile photo uploaded', 'error')
                    return redirect(url_for('admin_routes.add_user'))
            else:
                flash('No profile photo uploaded', 'error')
                return redirect(url_for('admin_routes.add_user'))
        
        return render_template('admin/add_user.html')
    else:
        flash('You are not authorized to access this page', 'error')
        return redirect(url_for('admin_routes.admin_dashboard'))

# Route to display the list of approved users
@admin_routes.route('/admin/user_list')
@login_required
def user_list():
    if session.get('user_type') == 'admin':
        # Filter users who are approved
        users = User.query.filter_by(is_approved=True).all()
        for user in users:
            if user.profile_photo:
                user.profile_photo = base64.b64encode(user.profile_photo).decode('utf-8')
        return render_template('admin/user_list.html', users=users)
    else:
        flash('Unauthorized access', 'error')
        return redirect(url_for('views.index'))

# Route to handle user deletion
@admin_routes.route('/admin/delete_user', methods=['POST'])
@login_required
def delete_user():
    if session.get('user_type') == 'admin':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            flash('User deleted successfully', 'success')
        else:
            flash('User not found', 'error')
        return redirect(url_for('admin_routes.user_list'))
    else:
        flash('Unauthorized access', 'error')
        return redirect(url_for('views.index'))


# Route to display registration requests to the admin
@admin_routes.route('/admin/registration_requests')
@login_required
def registration_requests():
    if session.get('user_type') == 'admin':
        registration_requests = User.query.filter_by(is_approved=False).all()
        
        # Convert profile photo to base64 for display
        for user in registration_requests:
            if user.profile_photo:
                user.profile_photo = base64.b64encode(user.profile_photo).decode('utf-8')
        
        return render_template('admin/user_requests.html', registration_requests=registration_requests)
    else:
        flash('Unauthorized access', 'error')
        return redirect(url_for('views.index'))


# Route to approve a registration request
@admin_routes.route('/admin/approve_registration/<int:user_id>', methods=['POST'])
@login_required
def approve_registration(user_id):
    if session.get('user_type') == 'admin':
        user = User.query.get(user_id)
        if user:
            user.is_approved = True
            db.session.commit()
            flash('Registration request approved successfully', 'success')
        else:
            flash('User not found', 'error')
        return redirect(url_for('admin_routes.registration_requests'))
    else:
        flash('Unauthorized access', 'error')
        return redirect(url_for('views.index'))

# Route to reject a registration request
@admin_routes.route('/admin/reject_registration/<int:user_id>', methods=['POST'])
@login_required
def reject_registration(user_id):
    if session.get('user_type') == 'admin':
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)  # Delete the user from the database
            db.session.commit()
            flash('Registration request rejected and user deleted successfully', 'success')
        else:
            flash('User not found', 'error')
        return redirect(url_for('admin_routes.registration_requests'))
    else:
        flash('Unauthorized access', 'error')
        return redirect(url_for('views.index'))

# Define route for adding a college
@admin_routes.route('/admin/add_college', methods=['GET', 'POST'])
def add_college():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form['name']
        location = request.form['location']
        
        # Create a new college object and add it to the database
        new_college = College(name=name, location=location)
        db.session.add(new_college)
        db.session.commit()
        
        # Redirect to the same page to display the updated list of colleges
        return redirect(url_for('admin_routes.add_college'))
    
    # Retrieve the list of colleges from the database
    colleges = College.query.all()
    
    # Render the HTML template for adding a college
    return render_template('admin/add_college.html', colleges=colleges)


@admin_routes.route('/admin/upload_excel', methods=['GET', 'POST'])
def upload_excel():
    colleges = College.query.all()
    if request.method == 'POST':
        # Handle file upload
        subject_list_file = request.files['subject_list']
        staff_list_file = request.files['staff_list']
        college_id = request.form['college']  # Obtain the selected college ID from the form
        
        # Parse Excel files and store data in the database
        parse_and_store_excel(subject_list_file, staff_list_file, college_id)
        
        # Redirect to a success page or homepage
        return redirect(url_for('admin_routes.admin_dashboard'))

    # If the request method is GET, render the upload_excel.html template
    return render_template('admin/upload_excel.html', colleges=colleges)

from sqlalchemy.exc import IntegrityError

def parse_and_store_excel(subject_list_file, staff_list_file, college_id):
    try:
        # Read subject list Excel file
        subject_df = pd.read_excel(subject_list_file)
        # Iterate through each row in the DataFrame
        for index, row in subject_df.iterrows():
            # Extract data from the row
            subject_name = row['subject_name']
            subject_code = row['subject_code']
            syllabus = row['syllabus']
            branch = row['branch']
            semester = row['semester']
            year = row['year']
            regulation = row['regulation']  # Added regulation
            integrated = row['integrated']  # Added integrated
            
            # Check if subject already exists
            existing_subject = SubjectList.query.filter_by(
                subject_code=subject_code,
                branch=branch,
                semester=semester,
                year=year,
                regulation=regulation,
                integrated=integrated
            ).first()

            if not existing_subject:
                # Create a new SubjectList object and add it to the database
                new_subject_list = SubjectList(
                    subject_name=subject_name,
                    subject_code=subject_code,
                    syllabus=syllabus,
                    college_id=college_id,
                    branch=branch,
                    semester=semester,
                    year=year,
                    regulation=regulation,
                    integrated=integrated
                )
                db.session.add(new_subject_list)
        
        # Commit changes for SubjectList
        db.session.commit()
        
        # Read staff list Excel file
        staff_df = pd.read_excel(staff_list_file)
        # Dictionary to track created users and staff
        user_dict = {}
        staff_dict = {}

        # Iterate through each row in the DataFrame
        for index, row in staff_df.iterrows():
            # Extract data from the row
            staff_name = row['Staff Name']
            email = row['Email']
            password = row['Password']
            handling_section = row['Handling Section']
            handling_subject_code = row['Handling Subject Code']
            role = row['Role']
            branch = row['Branch']

            # Check if the user already exists
            if email not in user_dict:
                # Create a new User object (for staff) and add it to the database
                new_user = User(
                    email=email,
                    name=staff_name,
                    college_id=college_id,
                    is_approved=True
                )
                new_user.set_password(password)  # Hash the password
                db.session.add(new_user)
                db.session.commit()  # Commit to get the user ID
                user_dict[email] = new_user
            else:
                new_user = user_dict[email]

            # Check if the staff already exists
            if email not in staff_dict:
                existing_staff = CollegeStaff.query.filter_by(email=email).first()
                if not existing_staff:
                    # Create a new CollegeStaff object and add it to the database
                    new_staff = CollegeStaff(
                        staff_name=staff_name,
                        email=email,
                        password=password,
                        handling_section=handling_section,
                        handling_subject_code=handling_subject_code,
                        role=role,
                        college_id=college_id,
                        branch=branch
                    )
                    db.session.add(new_staff)
                    db.session.commit()  # Commit to get the staff ID
                    staff_dict[email] = new_staff
                else:
                    new_staff = existing_staff
            else:
                new_staff = staff_dict[email]

            # Check if the subject with the same section and code already exists for this user
            existing_subject = Subject.query.filter_by(
                user_id=new_user.id,
                subject_code=handling_subject_code,
                section=handling_section
            ).first()

            if not existing_subject:
                # Find the subject associated with the handling subject code
                subject_list = SubjectList.query.filter_by(subject_code=handling_subject_code).first()
                if subject_list:
                    # Create a new Subject instance associated with the staff and user
                    new_subject = Subject(
                        subject_name=subject_list.subject_name,
                        faculty_name=staff_name,
                        branch=branch,
                        year=subject_list.year,
                        semester=subject_list.semester,
                        regulation=subject_list.regulation,
                        academic_year=subject_list.year,
                        section=handling_section,
                        integrated=subject_list.integrated,
                        user_id=new_user.id,
                        staff_id=new_staff.id,
                        subject_code=handling_subject_code,
                        college_id=college_id  # Added college_id
                    )
                    db.session.add(new_subject)

        # Commit changes to the database
        db.session.commit()

    except IntegrityError as e:
        # Handle IntegrityError (duplicate entry for email)
        print(f"IntegrityError: {e}")
        db.session.rollback()
    except Exception as e:
        # Handle other exceptions
        print(f"An error occurred: {e}")
        db.session.rollback()


@admin_routes.route('/admin/assessment_management')
@login_required
def assessment_management():
    colleges = College.query.all()
    subjects = Subject.query.all()  # Retrieve all subjects for the admin view
    return render_template('admin/assessment_management.html', colleges=colleges, subjects=subjects)

@admin_routes.route('/admin/add_assessment', methods=['POST'])
@login_required
def add_assessment():
    college_id = request.form['college_id']
    subject_code = request.form['subject_code']
    section = request.form['section']
    assessment_type = request.form['assessment_type']
    count = int(request.form['count'])
    max_marks = int(request.form['max_marks'])

    # Find the staff member who handles the subject for the selected section
    staff = CollegeStaff.query.filter_by(handling_subject_code=subject_code, handling_section=section, college_id=college_id).first()

    if not staff:
        flash('Staff member not found for the selected subject and section.', 'error')
        return redirect(url_for('admin_routes.assessment_management'))

    # Find the associated subject
    subject = Subject.query.filter_by(subject_code=subject_code, section=section, college_id=college_id).first()

    if not subject:
        flash('Subject not found.', 'error')
        return redirect(url_for('admin_routes.assessment_management'))

    if assessment_type == 'OTHER':
        name = f"{request.form['other_assessment_name'].upper()}({max_marks}M)"
    else:
        name = f"{assessment_type}({max_marks}M)"

    existing_assessment = Assessment.query.filter_by(
        name=name,
        max_marks=max_marks,
        subject_id=subject.id,
        user_id=staff.id  # Associate the assessment with the staff member who handles the subject
    ).first()

    if existing_assessment:
        existing_assessment.count += count
        db.session.commit()
        flash('Assessment count incremented successfully.', 'success')
    else:
        new_assessment = Assessment(name=name, count=count, max_marks=max_marks, subject=subject, user_id=staff.id, college_id=college_id)
        db.session.add(new_assessment)
        db.session.commit()
        flash('New assessment added successfully.', 'success')

        existing_instance_count = AssessmentInstance.query.filter_by(assessment_id=new_assessment.id).count()
        for i in range(1, count + 1):
            instance_name = f"{name} {existing_instance_count + i}"
            new_instance = AssessmentInstance(
                name=instance_name,
                assessment=new_assessment,
                user_id=staff.id,
                subject=subject,
                college_id=college_id
            )
            db.session.add(new_instance)
        db.session.commit()

    return redirect(url_for('admin_routes.assessment_management'))

@admin_routes.route('/admin/modify_assessment', methods=['POST'])
@login_required
def modify_assessment():
    action = request.form['action']
    assessment_id = int(request.form['assessment_id'])
    assessment = Assessment.query.filter_by(id=assessment_id).first_or_404()

    if action == 'delete_assessment':
        # Delete all instances associated with the assessment
        AssessmentInstance.query.filter_by(assessment_id=assessment.id).delete()
        db.session.delete(assessment)
        db.session.commit()
        flash('Assessment deleted successfully.', 'success')
    elif action == 'decrement_count':
        if assessment.count > 0:
            assessment.count -= 1
            instance_to_delete = AssessmentInstance.query.filter_by(assessment_id=assessment.id).order_by(AssessmentInstance.id.desc()).first()
            if instance_to_delete:
                db.session.delete(instance_to_delete)
                db.session.commit()
                flash('Count decremented successfully.', 'success')
        else:
            flash('Count cannot be decremented further.', 'error')
    elif action == 'increment_count':
        assessment.count += 1
        new_instance_name = f"{assessment.name} {assessment.count}"
        new_instance = AssessmentInstance(
            name=new_instance_name,
            assessment=assessment,
            staff_id=assessment.staff_id,  # Ensure the instance is associated with the correct staff
            subject=assessment.subject,
            college_id=assessment.college_id
        )
        db.session.add(new_instance)
        db.session.commit()
        flash('Count incremented successfully.', 'success')

    return redirect(url_for('admin_routes.assessment_management'))


@admin_routes.route('/get_subjects', methods=['GET'])
def get_subjects():
    college_id = request.args.get('college_id')
    subjects = Subject.query.filter_by(college_id=college_id).all()
    subject_data = [{'subject_code': subject.subject_code, 'subject_name': subject.subject_name} for subject in subjects]
    return jsonify({'subjects': subject_data})

@admin_routes.route('/get_sections_and_faculty', methods=['GET'])
def get_sections_and_faculty():
    subject_code = request.args.get('subject_code')
    subjects = Subject.query.filter_by(subject_code=subject_code).all()
    sections = list(set(subject.section for subject in subjects))
    return jsonify({'sections': sections})