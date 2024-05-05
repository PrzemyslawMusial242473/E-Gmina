from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__, static_folder='templates/static')
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Event
    
    with app.app_context():
        db.create_all()
        create_admin(app)
        
            
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login_user'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')
        
def create_admin(app):
    from .models import User
    from .auth import hash_password
    with app.app_context():
        admin_email = "elo@zelo"
        if User.query.filter_by(email=admin_email).first() is None:
            admin_password = "admin"
            admin = User(email=admin_email, password=hash_password(admin_password), role='admin',status="accepted")
            db.session.add(admin)
            db.session.commit()
            print("Admin account created successfully!")
        