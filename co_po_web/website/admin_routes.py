from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required
from werkzeug.security import generate_password_hash
import sys
sys.path.append('D:/co_po_web')
from website.models import User, Assessment,IAComponent, Section, College, CollegeStaff, SubjectList, Subject, AssessmentInstance
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
            regulation = row['regulation']
            integrated = row['integrated']
            
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

                    # Create and add a new Section if it doesn't exist
                    existing_section = Section.query.filter_by(
                        name=handling_section,
                        subject_code=handling_subject_code
                    ).first()

                    if not existing_section:
                        new_section = Section(
                            name=handling_section,
                            subject_code=handling_subject_code
                        )
                        db.session.add(new_section)

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


@admin_routes.route('/admin/ca_management', methods=['GET', 'POST'])
@login_required
def ca_management():
    colleges = College.query.all()
    subjects = []
    sections = []
    assessments = []
    ia_components = []

    selected_college_id = request.form.get('college') or request.args.get('college')
    selected_subject_id = request.form.get('subject') or request.args.get('subject')
    selected_section_id = request.form.get('section') or request.args.get('section')

    if selected_college_id:
        subjects = SubjectList.query.filter_by(college_id=selected_college_id).all()

    if selected_subject_id:
        subject = SubjectList.query.filter_by(id=selected_subject_id).first()
        if subject:
            sections = Section.query.filter_by(subject_code=subject.subject_code).all()

    if selected_section_id:
        assessments = db.session.query(
            Assessment, IAComponent, Section
        ).join(
            IAComponent, Assessment.ia_component_id == IAComponent.id
        ).join(
            Section, Assessment.section_id == Section.id
        ).filter(
            Assessment.college_id == selected_college_id,
            Assessment.subject_id == selected_subject_id,
            Assessment.section_id == selected_section_id
        ).all()

        if selected_subject_id and subject:
            ia_components = IAComponent.query.filter_by(
                college_id=selected_college_id,
                subject_code=subject.subject_code,
                section_id=selected_section_id
            ).all()

    return render_template(
        'admin/ca_management.html', 
        colleges=colleges, 
        subjects=subjects, 
        sections=sections, 
        assessments=assessments,
        ia_components=ia_components,
        selected_college_id=selected_college_id,
        selected_subject_id=selected_subject_id,
        selected_section_id=selected_section_id
    )


@admin_routes.route('/admin/add_assessment', methods=['POST'])
@login_required
def add_assessment():
    selected_college_id = request.form.get('college')
    selected_subject_id = request.form.get('subject')
    selected_section_id = request.form.get('section')

    if 'add_assessment' in request.form:
        cia_name = request.form.get('cia_name')
        cia_weightage = float(request.form.get('cia_weightage'))
        assessment_name = request.form.get('assessment_name')
        max_marks = int(request.form.get('max_marks'))
        assessment_weightage = float(request.form.get('assessment_weightage'))
        count = int(request.form.get('count'))

        if assessment_name == 'OTHER':
            assessment_name = request.form['other_assessment_name']

        if selected_college_id and selected_subject_id and selected_section_id and cia_name and assessment_name:
            try:
                # Check if the IA component already exists
                ia_component = IAComponent.query.filter_by(
                    name=cia_name,
                    college_id=selected_college_id,
                    subject_code=SubjectList.query.filter_by(id=selected_subject_id).first().subject_code,
                    section_id=selected_section_id
                ).first()

                if not ia_component:
                    # Create a new IA Component
                    ia_component = IAComponent(
                        name=cia_name,
                        weightage=cia_weightage,
                        college_id=selected_college_id,
                        subject_code=SubjectList.query.filter_by(id=selected_subject_id).first().subject_code,
                        section_id=selected_section_id
                    )
                    db.session.add(ia_component)
                    db.session.commit()

                # Create Assessment
                new_assessment = Assessment(
                    name=assessment_name,
                    max_marks=max_marks,
                    weightage=assessment_weightage,
                    count=count,
                    ia_component_id=ia_component.id,
                    subject_id=selected_subject_id,
                    college_id=selected_college_id,
                    section_id=selected_section_id
                )
                db.session.add(new_assessment)
                db.session.commit()

                # Create Assessment Instances
                for i in range(count):
                    instance_name = f"{assessment_name} {i+1}({max_marks})M"
                    new_assessment_instance = AssessmentInstance(
                        name=instance_name,
                        assessment_id=new_assessment.id,
                        instance_number=i+1,
                        subject_id=selected_subject_id,
                        college_id=selected_college_id,
                        section_id=selected_section_id
                    )
                    db.session.add(new_assessment_instance)
                    db.session.commit()

                flash('Assessments added successfully', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Error adding assessments', 'danger')
                print(e)

    return redirect(url_for('admin_routes.ca_management', college=selected_college_id, subject=selected_subject_id, section=selected_section_id))

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
        new_instance_name = f"{assessment.name} {assessment.count}({assessment.max_marks})M"  # Generate instance name with max marks
        new_instance = AssessmentInstance(
            name=new_instance_name,
            assessment_id=assessment.id,
            instance_number=assessment.count,
            subject_id=assessment.subject_id,
            college_id=assessment.college_id,
            section_id=assessment.section_id
        )
        db.session.add(new_instance)
        db.session.commit()
        flash('Count incremented successfully.', 'success')

    return redirect(url_for('admin_routes.ca_management', college=assessment.college_id, subject=assessment.subject_id, section=assessment.section_id))
