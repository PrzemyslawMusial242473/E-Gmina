
from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from . import db
from flask_login import login_user, login_required, logout_user, current_user
import hashlib


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
            if verify_password(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

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
        name = request.form.get('name')
        surname = request.form.get('surname')
        address = request.form.get('address')
        pesel = request.form.get('pesel')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('User already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(name) < 2:
            flash('Name must be greater than 1 character.', category='error')
        elif len(surname) < 2:
            flash('Surname must be greater than 1 character.', category='error')
        elif len(address) < 2:
            flash('Address name must be greater than 3 character.', category='error')
        elif len(pesel) != 11:
            flash('Pesel must contain exactly 11 digits.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, name=name, surname=surname,address=address,uid=pesel,password=hash_password(
                password1))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

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
        if user:
            flash('User already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(name) < 2:
            flash('Name must be greater than 1 character.', category='error')
        elif len(address) < 2:
            flash('Address name must be greater than 3 character.', category='error')
        elif len(nip) != 10:
            flash('NIP must contain exactly 10 digits.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, name=name,address=address,uid=nip,role='organisation',password=hash_password(
                password1))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up_org.html", user=current_user)
