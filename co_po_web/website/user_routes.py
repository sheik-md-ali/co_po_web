# user_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, jsonify, send_file
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import sys
sys.path.append('D:/co_po_web')
from website.models import User, Subject, Section, Assessment, AssessmentInstance, IAComponent, College, SubjectList
from io import BytesIO
from PIL import Image
import base64
from website import db
from openpyxl import Workbook
import io

user_routes = Blueprint('user_routes', __name__)

@user_routes.route('/user/dashboard')
@login_required
def user_dashboard():
    return render_template('user/user_dashboard.html')


@user_routes.route('/user_subjects')
@login_required
def user_subjects():
    # Retrieve subjects for the current user by querying the database
    user_subjects = Subject.query.filter_by(user_id=current_user.id).all()

    return render_template('user/user_subjects.html', user_subjects=user_subjects)


@user_routes.route('/user/mapping_for_assessment', methods=['GET', 'POST'])
@login_required
def mapping_for_assessment():
    # Query distinct subject codes associated with the current user
    subject_codes = db.session.query(Subject.subject_code).filter_by(user_id=current_user.id).distinct().all()

    # Convert list of tuples to list of subject codes
    subject_codes = [code[0] for code in subject_codes]

    selected_subject_code = request.form.get('subject_code')
    selected_section_name = request.form.get('section')
    selected_assessment_instance_id = request.form.get('assessment_instance')

    sections = []
    assessment_instances = []
    assessment_details = None

    if selected_subject_code:
        # Query the sections based on the selected subject code and current user
        sections = db.session.query(Section).join(Subject, Section.subject_code == Subject.subject_code).filter(
            Subject.user_id == current_user.id,
            Subject.subject_code == selected_subject_code,
            Section.name == Subject.section
        ).all()


        if selected_section_name:
            # Query assessment instances based on the selected subject code and section name
            section = db.session.query(Section).join(Subject, Section.subject_code == Subject.subject_code).filter(
                Subject.user_id == current_user.id,
                Section.subject_code == selected_subject_code,
                Section.name == selected_section_name
            ).first()
            if section:
                assessment_instances = AssessmentInstance.query.filter_by(section_id=section.id).all()

                if selected_assessment_instance_id:
                    # Query assessment details if a specific instance is selected
                    assessment_instance = AssessmentInstance.query.get(selected_assessment_instance_id)
                    if assessment_instance:
                        assessment_details = {
                            'name': assessment_instance.name,
                            'max_marks': assessment_instance.assessment.max_marks
                        }

    return render_template('user/mapping_for_assessment.html', subjects=subject_codes, sections=sections,
                           assessment_instances=assessment_instances, assessment_details=assessment_details,
                           selected_subject_code=selected_subject_code, selected_section_name=selected_section_name,
                           selected_assessment_instance_id=selected_assessment_instance_id)


@user_routes.route('/user/save_or_submit_assessment', methods=['POST'])
@login_required
def save_or_submit_assessment():
    selected_subject_code = request.form.get('selected_subject_code')
    selected_section_name = request.form.get('selected_section_name')
    selected_assessment_instance_id = request.form.get('selected_assessment_instance_id')
    action = request.form.get('action')

    assessment_instance = AssessmentInstance.query.get(selected_assessment_instance_id)
    if not assessment_instance:
        flash('Assessment instance not found.', 'error')
        return redirect(url_for('user_routes.mapping_for_assessment'))

    if assessment_instance.status_for_mapping == 'submitted':
        flash('Assessment already submitted. Cannot modify further.', 'error')
        return redirect(url_for('user_routes.mapping_for_assessment'))

    mapping_dict = {}
    question_count = int(request.form.get('question_count', 0))


    for i in range(1, question_count + 1):
        max_marks = request.form.get(f'question{i}_maxMarks')
        co_selected = request.form.get(f'question{i}_co')

        if max_marks and co_selected:
            mapping_dict[f'Q{i}'] = {
                'maxMarks': max_marks,
                'co': co_selected
            }


    assessment_instance.mapping_dictionary = mapping_dict

    if action == 'submit':
        assessment_instance.status_for_mapping = 'submitted'
        flash('Assessment submitted successfully.', 'success')
    else:
        assessment_instance.status_for_mapping = 'saved'
        flash('Mapping saved successfully.', 'success')

    db.session.commit()

    return redirect(url_for('user_routes.mapping_for_assessment'))


@user_routes.route('/user/upload_excel', methods=['GET', 'POST'])
@login_required
def upload_excel():
    subject_codes = db.session.query(Subject.subject_code).filter_by(user_id=current_user.id).distinct().all()
    subject_codes = [code[0] for code in subject_codes]

    selected_subject_code = request.form.get('subject_code')
    selected_section_name = request.form.get('section')
    selected_assessment_instance_id = request.form.get('assessment_instance')

    sections = []
    assessment_instances = []
    assessment_details = None

    if selected_subject_code:
        sections = db.session.query(Section).join(Subject, Section.subject_code == Subject.subject_code).filter(
            Subject.user_id == current_user.id,
            Subject.subject_code == selected_subject_code,
            Section.name == Subject.section
        ).all()

        if selected_section_name:
            section = db.session.query(Section).join(Subject, Section.subject_code == Subject.subject_code).filter(
                Subject.user_id == current_user.id,
                Section.subject_code == selected_subject_code,
                Section.name == selected_section_name
            ).first()
            if section:
                assessment_instances = AssessmentInstance.query.filter_by(section_id=section.id).all()

                if selected_assessment_instance_id:
                    assessment_instance = AssessmentInstance.query.get(selected_assessment_instance_id)
                    if assessment_instance:
                        assessment_details = {
                            'name': assessment_instance.name,
                            'max_marks': assessment_instance.assessment.max_marks
                        }

    return render_template('user/upload_excel.html', subjects=subject_codes, sections=sections,
                           assessment_instances=assessment_instances, assessment_details=assessment_details,
                           selected_subject_code=selected_subject_code, selected_section_name=selected_section_name,
                           selected_assessment_instance_id=selected_assessment_instance_id)

@user_routes.route('/user/upload_excel_file', methods=['POST'])
@login_required
def upload_excel_file():
    selected_assessment_instance_id = request.form.get('assessment_instance')
    action = request.form.get('action')

    if not selected_assessment_instance_id:
        flash('No assessment instance selected.', 'danger')
        return redirect(url_for('user_routes.upload_excel'))

    assessment_instance = AssessmentInstance.query.get(selected_assessment_instance_id)

    if 'assessmentfile' not in request.files:
        flash('No file part in the request.', 'danger')
        return redirect(url_for('user_routes.upload_excel'))

    file = request.files['assessmentfile']
    if file.filename == '':
        flash('No selected file.', 'danger')
        return redirect(url_for('upload_excel'))

    if file:
        filename = secure_filename(file.filename)
        file_data = file.read()

        if action == 'submit' and assessment_instance.status_for_excel != 'submitted':
            assessment_instance.excel_file = file_data
            assessment_instance.status_for_excel = 'submitted'
            db.session.commit()
            flash('Assessment file submitted successfully and cannot be modified further.', 'success')
            return redirect(url_for('user_routes.upload_excel'))
        elif action == 'save' and assessment_instance.status_for_excel != 'submitted':
            assessment_instance.excel_file = file_data
            assessment_instance.status_for_excel = 'saved'
            db.session.commit()
            flash('Assessment file saved successfully.', 'success')
            return redirect(url_for('user_routes.upload_excel'))
        else:
            flash('Assessment file cannot be modified as it is already submitted.', 'danger')
            return redirect(url_for('user_routes.upload_excel'))
        
        
@user_routes.route('/download/template.xlsx', methods=['GET'])
@login_required
def download_template():
    selected_assessment_instance_id = request.args.get('assessment_instance_id')
    
    if not selected_assessment_instance_id:
        flash('Please select an assessment instance.')
        return redirect(url_for('user_routes.upload_excel'))

    # Fetch assessment instance and associated mapping JSON
    assessment_instance = AssessmentInstance.query.get(selected_assessment_instance_id)
    if not assessment_instance:
        flash('Invalid assessment instance ID.')
        return redirect(url_for('user_routes.upload_excel'))
    
    mapping = assessment_instance.mapping_dictionary

    # Fetch necessary details for the template
    college = College.query.get(assessment_instance.college_id)
    subject = SubjectList.query.get(assessment_instance.subject_id)
    #user = User.query.get(subject.user_id)

    # Create a new Excel workbook and select the active sheet
    wb = Workbook()
    sheet = wb.active
    sheet.title = 'Assessment Template'

    # Write header information
    sheet['A1'] = college.name
    sheet.merge_cells('A1:F1')

    # Add Year, Branch, and Semester in the second row
    sheet['A2'] = f"Year: {subject.year}  Branch: {subject.branch}  Semester: {subject.semester}"
    sheet.merge_cells('A2:F2')

    # Write subject code and subject name in the third row
    sheet['A3'] = f"SUBJECT CODE : {subject.subject_code}                     | SUBJECT NAME: {subject.subject_name}"
    sheet.merge_cells('A3:F3')

    # Write COs and Max Marks headers in the fourth and fifth rows
    sheet['B5'] = "CO's"
    sheet['B6'] = 'MAX MARKS'

    question_columns = list(mapping.keys())
    
    # Populate COs and Max Marks based on mapping
    for index, question in enumerate(question_columns, start=2):
        sheet.cell(row=5, column=index + 1).value = mapping[question].get('co', '')  # COs
        sheet.cell(row=6, column=index + 1).value = mapping[question].get('maxMarks', '')  # Max Marks

    # Write SNO, REG NO, and Q1, Q2, ... headers in the seventh row
    sheet['A7'] = 'SNO'
    sheet['B7'] = 'REG NO'

    for index, _ in enumerate(question_columns, start=1):
        sheet.cell(row=7, column=index + 2).value = f"Q{index}"

    # Save workbook to a BytesIO object to send it as a downloadable file
    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)

    return send_file(
        excel_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='assessment_template.xlsx'
    )


 