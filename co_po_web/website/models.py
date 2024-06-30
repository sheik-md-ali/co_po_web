import sys
sys.path.append('D:/co_po_web')
from website import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# User Model
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
        return check_password_hash(self.password)

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

# Assessment Model
class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    count = db.Column(db.Integer, nullable=False)
    max_marks = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('assessments', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('assessments', lazy=True))
    college = db.relationship('College', backref=db.backref('assessments', lazy=True))

    def __repr__(self):
        return f"Assessment(name='{self.name}', count={self.count}, max_marks={self.max_marks})"

# AssessmentInstance Model
class AssessmentInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)

    assessment = db.relationship('Assessment', backref=db.backref('instances', lazy=True))
    user = db.relationship('User', backref=db.backref('assessment_instances', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('assessment_instances', lazy=True))
    college = db.relationship('College', backref=db.backref('assessment_instances', lazy=True))

    excel_file = db.Column(db.LargeBinary)
    mapping_dictionary = db.Column(db.PickleType)

    def __repr__(self):
        return f"AssessmentInstance(name='{self.name}')"

# IAComponent Model
class IAComponent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    assessment_instance_id = db.Column(db.Integer, db.ForeignKey('assessment_instance.id'), nullable=False)

    assessment_instance = db.relationship('AssessmentInstance', backref=db.backref('ia_components', lazy=True))
