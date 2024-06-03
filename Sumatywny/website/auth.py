
from flask import Blueprint, render_template, request, flash, redirect, url_for,send_file,make_response
from .models import User,ALLOWED_EXTENSIONS
from flask_login import login_user, login_required, logout_user, current_user
import hashlib
from werkzeug.utils import secure_filename
from .views import send_confirmation_email
from io import BytesIO
from . import db

auth = Blueprint('auth', __name__)

def hash_password(password):
    hash_object = hashlib.sha256()
    hash_object.update(password.encode())
    hashed_password = hash_object.hexdigest()
    return hashed_password

def verify_password(hashed_password, user_password):
    hash_object = hashlib.sha256()
    hash_object.update(user_password.encode())
    user_hashed_password = hash_object.hexdigest()
    return hashed_password == user_hashed_password


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if user.status != "rejected":
                if user.status == "accepted":
                    if verify_password(user.password, password):
                        flash('Zalogowano!', category='success')
                        login_user(user, remember=True)
                        return redirect(url_for('views.home'))
                    else:
                        flash('Błędne hasło spróbuj ponownie.', category='error')
                else:
                    flash('Twoje konto nie zostało jeszcze zatwierdzone.', category='error')
            else:
                flash('Twoje konto zostało odrzucone.', category='error')
        else:
            flash('Email jest błędny.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def choose_signup():
    return render_template("sign_up_type.html", user=current_user)


@auth.route('/sign-up/user', methods=['GET', 'POST'])
def sign_up_user():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        name = request.form.get('name')
        surname = request.form.get('surname')
        address = request.form.get('address')
        pesel = request.form.get('pesel')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        document_image = request.files.get('document_image')

        user = User.query.filter_by(email=email).first()
        check_pesel = User.query.filter_by(uid=pesel).first()
        check_username = User.query.filter_by(username=username).first()

        if user:
            flash('Konto już istnieje.', category='error')
        elif len(email) < 3:
            flash('Email musi mieć więcej niż 3 znaki.', category='error')
        elif len(username) < 3:
            flash('Nazwa użytkownika musi mieć więcej niż 3 znaki.', category='error')
        elif check_username:
            flash('Nazwa użytkownika już istnieje.', category='error')
        elif len(name) < 2:
            flash('Imię musi być dłuższe niż 2 znaki.', category='error')
        elif len(surname) < 2:
            flash('Nazwisko musi być dłuższe niż 2 znaki.', category='error')
        elif len(address) < 2:
            flash('Adres musi być dłuższy niż 2 znaki.', category='error')
        elif len(pesel) != 11:
            flash('Pesel musi posiadać równo 11 liczb.', category='error')
        elif check_pesel:
            flash('Pesel już istnieje.', category='error')
        elif password1 != password2:
            flash('Hasła nie są takie same.', category='error')
        elif len(password1) < 7:
            flash('Hasło musi się składać z 7 znaków.', category='error')
        elif document_image and allowed_file(document_image.filename):
            document_image_data = document_image.read()
            new_user = User(email=email, username=username, name=name, surname=surname, address=address,
                            uid=pesel, password=hash_password(password1), document_image=document_image_data)
            db.session.add(new_user)
            db.session.commit()
            send_confirmation_email(new_user)
            flash('Konto musi przejść jeszcze etap zatwierdzenia!', category='success')
            return redirect(url_for('views.home'))
        else:
            flash('Nieprawidłowy plik obrazu.', category='error')
    
    return render_template("sign_up_user.html", user=current_user)

@auth.route('/sign-up/org', methods=['GET', 'POST'])
def sign_up_org():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        address = request.form.get('address')
        nip = request.form.get('nip')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        check_nip = User.query.filter_by(uid=nip).first()
        if user:
            flash('Konto już istnieje.', category='error')
        elif len(email) < 3:
            flash('Email musi mieć więcej niż 3 znaki.', category='error')
        elif len(name) < 2:
            flash('Imię musi być dłuższe niż 2 znaki.', category='error')
        elif len(address) < 2:
            flash('Adres musi być dłuższy niż 2 znaki.', category='error')
        elif len(nip) != 10:
            flash('NIP musi posiadać równo 10 liczb.', category='error')
        elif check_nip:
            flash('NIP już istnieje.', category='error')
        elif password1 != password2:
            flash('Hasła nie są takie same.', category='error')
        elif len(password1) < 7:
            flash('Hasło musi się składać z 7 znaków.', category='error')
        else:
            new_user = User(email=email, name=name,address=address,uid=nip,role='organisation',password=hash_password(
                password1))
            db.session.add(new_user)
            db.session.commit()
            send_confirmation_email(new_user)
            flash('Konto musi przejść jeszcze etap zatwierdzenia!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up_org.html", user=current_user)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth.route('/document-image/<int:user_id>')
def get_document_image(user_id):
    user = User.query.get_or_404(user_id)
    if user.document_image:
        return send_file(BytesIO(user.document_image), mimetype='image/jpeg')
    else:
        return make_response("No image found", 404)
