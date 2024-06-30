import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import sys
sys.path.append('D:/co_po_web')
# Initialize SQLAlchemy instance
db = SQLAlchemy()

def create_app():
    load_dotenv()  # Load environment variables from .env file

    # Initialize Flask app
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'qwertyuiopzxcvbnmlkjhgfdsa')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'mysql://root:6381!Root$$@localhost/co_po')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Import Blueprints
    from website.views import views
    from website.auth import auth
    from website.admin_routes import admin_routes
    from website.user_routes import user_routes

    # Register Blueprints
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin_routes, url_prefix='/admin')
    app.register_blueprint(user_routes, url_prefix='/user')

    # Create database tables
    with app.app_context():
        db.init_app(app)
        db.create_all()

        # Check if admin details exist in .env file
        from website.models import Admin
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')
        if admin_email and admin_password:
            existing_admin = Admin.query.filter_by(email=admin_email).first()
            if not existing_admin:
                admin_user = Admin(email=admin_email, is_main_admin=True)
                admin_user.set_password(admin_password)
                db.session.add(admin_user)
                db.session.commit()

    # Initialize LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from website.models import User, Admin
        user = User.query.get(user_id)
        if user:
            return user
        else:
            admin = Admin.query.get(user_id)
            return admin

    return app
