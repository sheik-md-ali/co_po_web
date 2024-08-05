import sys
sys.path.append('D:/co_po_web')
from website import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import JSON

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    mobile_no = db.Column(db.String(20), nullable=True)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    profile_photo = db.Column(db.LargeBinary)
    is_approved = db.Column(db.Boolean, default=False)

    college = db.relationship('College', backref=db.backref('users', lazy=True))

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# Admin Model
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_main_admin = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# College Model
class College(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)

# CollegeStaff Model
class CollegeStaff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    handling_section = db.Column(db.String(100), nullable=False)
    handling_subject_code = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    branch = db.Column(db.String(100), nullable=False)

    college = db.relationship('College', backref=db.backref('staff', lazy=True))

    def __init__(self, staff_name, email, password, handling_section, handling_subject_code, role, college_id, branch):
        self.staff_name = staff_name
        self.email = email
        self.password = generate_password_hash(password)
        self.handling_section = handling_section
        self.handling_subject_code = handling_subject_code
        self.role = role
        self.college_id = college_id
        self.branch = branch

# Subject Model

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False)
    faculty_name = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(100), nullable=False)
    regulation = db.Column(db.String(100), nullable=False)
    academic_year = db.Column(db.String(100), nullable=False)
    section = db.Column(db.String(100), nullable=False)
    integrated = db.Column(db.String(3), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('college_staff.id'), nullable=False)
    subject_code = db.Column(db.String(100), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
   
    user = db.relationship('User', backref=db.backref('subjects', lazy=True))
    staff = db.relationship('CollegeStaff', backref=db.backref('subjects', lazy=True))
    college = db.relationship('College', backref=db.backref('subjects', lazy=True))


# SubjectList Model
class SubjectList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False)
    subject_code = db.Column(db.String(100), nullable=False)
    syllabus = db.Column(db.Text, nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    regulation = db.Column(db.String(100), nullable=False)
    integrated = db.Column(db.String(3), nullable=False)

    college = db.relationship('College', backref=db.backref('subject_lists', lazy=True))

# Section Model
class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject_code = db.Column(db.String(50), nullable=False)  # Add subject_code field


    def __init__(self, name, subject_code):
        self.name = name
        self.subject_code = subject_code



class IAComponent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    weightage = db.Column(db.Float, nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    subject_code = db.Column(db.String(100), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)

    college = db.relationship('College', backref=db.backref('ia_components', lazy=True))
    section = db.relationship('Section', backref=db.backref('ia_components', lazy=True))

    def __repr__(self):
        return f"IAComponent(name='{self.name}', weightage={self.weightage})"


class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    max_marks = db.Column(db.Integer, nullable=False)
    weightage = db.Column(db.Float, nullable=False)
    count = db.Column(db.Integer, nullable=False)  # Number of instances
    ia_component_id = db.Column(db.Integer, db.ForeignKey('ia_component.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)

    ia_component = db.relationship('IAComponent', backref=db.backref('assessments', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('assessments', lazy=True))
    college = db.relationship('College', backref=db.backref('assessments', lazy=True))
    section = db.relationship('Section', backref=db.backref('assessments', lazy=True))

    def __repr__(self):
        return f"Assessment(name='{self.name}', max_marks={self.max_marks}, weightage={self.weightage}, count={self.count})"



class AssessmentInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=False)
    instance_number = db.Column(db.Integer, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    excel_file = db.Column(db.LargeBinary)
    mapping_dictionary = db.Column(JSON)
    status_for_mapping = db.Column(db.String(20), nullable=False, default='saved')
    status_for_excel = db.Column(db.String(20), nullable=False, default='saved')

    assessment = db.relationship('Assessment', backref=db.backref('instances', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('assessment_instances', lazy=True))
    college = db.relationship('College', backref=db.backref('assessment_instances', lazy=True))
    section = db.relationship('Section', backref=db.backref('assessment_instances', lazy=True))

    def __repr__(self):
        return f"AssessmentInstance(name='{self.name}', instance_number={self.instance_number})"
    

class CoAttainment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    subject_code = db.Column(db.String(100), nullable=False)
    total_students = db.Column(db.Integer, nullable=False)
    batch = db.Column(db.String(100), nullable=False)
    target_perc =db.Column(db.Integer, nullable=False)
    co_data = db.Column(db.JSON, nullable=False)
    loa_data = db.Column(db.JSON, nullable=False)
    practical_component = db.Column(db.String(10), nullable=False)
    practical_data = db.Column(db.JSON)
    theory_marks = db.Column(db.Float, nullable=False)
    theory_percentage = db.Column(db.Float, nullable=False)
    practical_marks = db.Column(db.Float, nullable=False)
    practical_percentage = db.Column(db.Float, nullable=False)
    ia_percentage = db.Column(db.Float, nullable=False)
    ese_percentage = db.Column(db.Float, nullable=False)
    TcourseExitSurveyPercentage = db.Column(db.Float, nullable=False)
    prac_ia_percentage = db.Column(db.Float, nullable=False)
    prac_ese_percentage = db.Column(db.Float, nullable=False)
    practicalCourseExitSurveyPercentage = db.Column(db.Float, nullable=False)
    copo_mappings = db.Column(db.JSON, nullable=False)  
    pso_mappings = db.Column(db.JSON, nullable=False)  
    

    college = db.relationship('College', backref=db.backref('co_attainments', lazy=True))


class InternalAssessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    assessment_instance_ids = db.Column(db.JSON, nullable=False)
    assessment_instance_ids_practical = db.Column(db.JSON, nullable=False) 
    co_values = db.Column(db.JSON, nullable=True)   
    weightage_co_values = db.Column(db.JSON, nullable=True)  # JSON column to store weightage CO values
    target_counts = db.Column(db.JSON, nullable=True)  
    college = db.relationship('College', backref=db.backref('internal_assessments', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('internal_assessments', lazy=True))
    section = db.relationship('Section', backref=db.backref('internal_assessments', lazy=True))

    def __repr__(self):
        return f"InternalAssessment(college_id={self.college_id}, subject_id={self.subject_id}, section_id={self.section_id})"
    


class SemesterEndExam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    co_values = db.Column(db.JSON, nullable=True)   
    target_counts = db.Column(db.JSON, nullable=True)  
    college = db.relationship('College', backref=db.backref('semester_end_exams', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('semester_end_exams', lazy=True))
    section = db.relationship('Section', backref=db.backref('semester_end_exams', lazy=True))

    def __repr__(self):
        return f"SemesterEndExam(college_id={self.college_id}, subject_id={self.subject_id}, section_id={self.section_id})"

class CourseExitSurvey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    co_values = db.Column(db.JSON, nullable=True)   
    target_counts = db.Column(db.JSON, nullable=True)  
    college = db.relationship('College', backref=db.backref('course_exit_surveys', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('course_exit_surveys', lazy=True))
    section = db.relationship('Section', backref=db.backref('course_exit_surveys', lazy=True))

    def __repr__(self):
        return f"CourseExitSurvey(college_id={self.college_id}, subject_id={self.subject_id}, section_id={self.section_id})"
