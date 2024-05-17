import requests
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Event, MapMarker, User, Message,Report, Survey, Answer, Question
from datetime import datetime
from . import db
import json
import calendar
import datetime
import stripe

views = Blueprint('views', __name__)

def get_month_events(year, month):
    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month, calendar.monthrange(year, month)[1])
    month_events = Event.query.filter(Event.date.between(start_date, end_date)).all()
    return month_events


def generate_calendar(year, month, month_events):
    cal = calendar.monthcalendar(year, month)
    weeks = []
    for week in cal:
        current_week = []
        for day in week:
            events_for_day = [event for event in month_events if event.date.day == day]
            current_week.append((day, events_for_day))
        weeks.append(current_week)
    return weeks


import calendar

@views.route('/', methods=['GET', 'POST'])
def home():
    today = datetime.date.today()
    year = today.year
    month = today.month

    # Sprawdź, czy został przesłany formularz z informacją o zmianie miesiąca
    if request.method == 'GET':
        if 'prev_month' in request.args:
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        elif 'next_month' in request.args:
            month += 1
            if month == 13:
                month = 1
                year += 1

    month_events = get_month_events(year, month)
    accepted_month_events = [event for event in month_events if event.status == 'accepted']
    weeks = generate_calendar(year, month, accepted_month_events)
    accepted_events = Event.query.filter_by(status='accepted').all()
    markers = MapMarker.query.all()  # Pobieramy wszystkie znaczniki z bazy danych

    # Pobierz nazwę aktualnego miesiąca po polsku
    current_month_name = calendar.month_name[month]

    return render_template("home.html", calendar=weeks, current_month=current_month_name, user=current_user,
                           accepted_events=accepted_events, markers=markers)



@views.route('/delete-event', methods=['POST'])
def delete_event():  
    event = json.loads(request.data)
    eventId = event['eventId']
    event = Event.query.get(eventId)
    if event:
        if event.user_id == current_user.id:
            db.session.delete(event)
            db.session.commit()

    return jsonify({})


@views.route('/calendar', methods=['GET'])
def calendar_view():
    today = datetime.date.today()
    current_month = today.strftime("%B")
    year = today.year
    month = today.month
    month_events = get_month_events(year, month)
    accepted_month_events = [event for event in month_events if event.status == 'accepted']
    weeks = generate_calendar(year, month, accepted_month_events)
    return render_template("calendar.html", user=current_user, calendar=weeks, current_month=current_month)


@views.route('/maps', methods=['GET', 'POST'])
def maps():
    if request.method == 'POST':
        address = request.form['address']
        description = request.form['description']
        api_key = 'AIzaSyDgRv7f0CZS1zchzAV9WsXTMRrCmIHxY_M'
        geocoding_url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}'

        response = requests.get(geocoding_url)
        data = response.json()

        if data['status'] == 'OK':
            lat = data['results'][0]['geometry']['location']['lat']
            lng = data['results'][0]['geometry']['location']['lng']

            new_marker = MapMarker(lat=lat, lng=lng, address=address, description=description, user_id=current_user.id)
            db.session.add(new_marker)
            db.session.commit()

            flash('Znacznik dodany pomyślnie', category='success')
            return redirect(url_for('views.maps'))
        else:
            flash('Nie znaleziono koordynatów dla podanego adresu', category='error')
            return redirect(url_for('views.maps'))

    markers = MapMarker.query.all()  # Pobieramy wszystkie znaczniki z bazy danych
    return render_template("maps.html", user=current_user, markers=markers)

@views.route('/delete-marker/<int:marker_id>', methods=['POST'])
def delete_marker(marker_id):
    marker = MapMarker.query.get(marker_id)
    if marker:
        db.session.delete(marker)
        db.session.commit()
        flash('Znacznik usunięty pomyślnie', category='success')
    else:
        flash('Znacznik nie został znaleziony', category='error')
    return redirect(url_for('views.maps'))

@views.route('/events', methods=['GET', 'POST'])
@login_required
def event():
    user_events = current_user.Events
    if request.method == 'POST':
        data = request.form.get('data')
        date = request.form.get('date')
        place = request.form.get('place')
        name = request.form.get('name')
        
        if data and date and place and name:
            try:
                date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M')
            except ValueError:
                return 'Zły format daty'
            
            new_event = Event(data=data, date=date, place=place, name=name, user_id=current_user.id, status='pending')
            db.session.add(new_event) 
            db.session.commit()  
            flash('Wydarzenie zawnioskowano!', category='success')
            
            
            return redirect(url_for('views.event'))  
    
    return render_template('events.html', user=current_user,user_events=user_events)


@views.route('/invite-friends', methods=['GET', 'POST'])
@login_required
def search_user():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            if user == current_user:
                flash('Nie możesz dodać samego siebie jako znajomego!', category='error')
            else:
                if user in current_user.friends:
                    flash(f'{user.username} jest już twoim znajomym!', category='error')
                elif user in current_user.sent:
                    flash(f'Zaproszenie wysłano do {user.username}!', category='error')
                elif user in current_user.invitations:
                    flash(f'Zaproszenie otrzymane od {user.username}!', category='error')
                elif user in current_user.blocked:
                    flash(f'{user.username} jest zablokowany!', category='error')
                elif user in current_user.y_blocked:
                    flash(f'Zostałeś zablokowany przez {user.username}!', category='error')
                elif user.role == 'admin':
                    flash(f'Nie można wysłać wiadomości do admina!', category='error')
                elif user.role == 'organisation':
                    flash(f'Nie można wysłać wiadomości do organizacji!', category='error')
                else:
                    current_user.sent.append(user)
                    user.invitations.append(current_user)
                    db.session.commit()
                    flash(f'Zaproszenie pomyślnie wysłano do {user.username}!', category='success')
        else:
            flash('Użytkownik nie został znaleziony!', category='error')
        return redirect(url_for('views.search_user'))
    return render_template('invite-friends.html', user=current_user)


@views.route('/send-message/<int:user_id>', methods=['POST'])
@login_required
def send_message(user_id):
    if request.method == 'POST':
        content = request.form.get('content')
        receiver = User.query.get(user_id)
        if receiver:
            new_message = Message(sender_id=current_user.id, receiver_id=user_id, content=content)
            db.session.add(new_message)
            db.session.commit()
            flash('Wiadomość została wysłana!', category='success')
            return redirect(url_for('views.user_chat', user_id=user_id))
        else:
            flash('Nie znaleziono użytkownika.', category='error')
    return redirect(url_for('views.home'))


@views.route('/remove-friend/<int:friend_id>', methods=['POST'])
@login_required
def remove_friend(friend_id):
    friend = User.query.get(friend_id)
    if friend:
        current_user.friends.remove(friend)
        friend.friends.remove(current_user)
        db.session.commit()
        flash(f'{friend.username} został usunięty z listy znajomych.', category='success')
    else:
        flash('Nie znaleziono użytkownika.', category='error')
    return redirect(url_for('views.search_user'))


@views.route('/block-user/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    user = User.query.get(user_id)
    if user:
        if user in current_user.friends:
            current_user.blocked.append(user)
            user.y_blocked.append(current_user)
            current_user.friends.remove(user)
            user.friends.remove(current_user)
            db.session.commit()
            flash(f'{user.username} został zablokowany.', category='success')
        else:
            current_user.blocked.append(user)
            user.y_blocked.append(current_user)
            current_user.invitations.remove(user)
            user.sent.remove(current_user)
            db.session.commit()
            flash(f'{user.username} został zablokowany.', category='success')
    else:
        flash('Nie znaleziono użytkownika.', category='error')
    return redirect(url_for('views.search_user'))


@views.route('/unblock-user/<int:user_id>', methods=['POST'])
@login_required
def unblock_user(user_id):
    user = User.query.get(user_id)
    if user:
        if user in current_user.blocked:
            current_user.blocked.remove(user)
            user.y_blocked.remove(current_user)
            db.session.commit()
            flash(f'{user.username} został odblokowany.', category='success')
        else:
            flash('Użytkownik nie jest zablokowany.', category='error')
    else:
        flash('Nie znaleziono użytkownika.', category='error')
    return redirect(url_for('views.search_user'))


@views.route('/chat/<int:user_id>', methods=['GET'])
@login_required
def user_chat(user_id):
    receiver = User.query.get(user_id)
    if not receiver:
        flash('Nie znaleziono użytkownika.', category='error')
        return redirect(url_for('views.home'))
    #username = request.form.get('username')
    #user = User.query.filter_by(username=username).first()
    elif receiver in current_user.y_blocked:
        flash(f'Zostałeś zablokowany przez {receiver.username}!', category='error')
        return redirect(url_for('views.search_user'))
    elif receiver not in current_user.friends:
        flash(f'{receiver.username} nie jest już twoim znajomym!', category='error')
        return redirect(url_for('views.search_user'))
    messages_sent_by_user = Message.query.filter_by(sender_id=current_user.id, receiver_id=user_id).all()
    messages_received_by_user = Message.query.filter_by(sender_id=user_id, receiver_id=current_user.id).all()
    messages = messages_sent_by_user + messages_received_by_user
    messages.sort(key=lambda x: x.timestamp)

    return render_template('user_chat.html', user=current_user, receiver=receiver, messages=messages)


@views.route('/accept-invite', methods=['POST'])
@login_required
def accept_invite():
    data = json.loads(request.data)
    inviter_email = data['inviter_email']
    inviter = User.query.filter_by(username=inviter_email).first()
    if inviter in current_user.invitations:
        current_user.invitations.remove(inviter)
        current_user.friends.append(inviter)
        inviter.friends.append(current_user)
        inviter.sent.remove(current_user)
        db.session.commit()
    return jsonify({})


@views.route('/reject-invite', methods=['POST'])
@login_required
def reject_invite():
    data = json.loads(request.data)
    inviter_email = data['inviter_email']
    inviter = User.query.filter_by(username=inviter_email).first()
    if inviter in current_user.invitations:
        current_user.invitations.remove(inviter)
        inviter.sent.remove(current_user)
        db.session.commit()
    return jsonify({})

@views.route('/admin-events', methods=['GET', 'POST'])
@login_required
def admin_events():
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Nie masz uprawnień administratora do tej strony.', category='danger')
        return redirect(url_for('views.home'))
    
    pending_events = Event.query.filter_by(status='pending').all()
    
    if request.method == 'POST':
        event_id = request.form.get('event_id')
        action = request.form.get('action')  
        
        if action == 'accept':
            event = Event.query.get(event_id)
            event.status = 'accepted'
            db.session.add(event)
            db.session.commit()
            flash('Wydarzenie zostało zaakceptowane.', category='success')
        elif action == 'reject':
            event = Event.query.get(event_id)
            event.status = 'rejected'
            flash('Wydarzenie zostało odrzucone.', category='warning')
        
        return redirect(url_for('views.admin_events'))

    return render_template('admin_events.html',user=current_user, pending_events=pending_events)

@views.route('/update_event_status/<int:event_id>/<string:action>', methods=['POST'])
@login_required
def update_event_status(event_id, action):
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Nie masz uprawnień administratora do tej akcji.', category='danger')
        return redirect(url_for('views.admin_events'))

    event = Event.query.get(event_id)
    if not event:
        flash('Nie znaleziono wydarzenia.', category='danger')
        return redirect(url_for('views.admin_events'))

    if action == 'accept':
        event.status = 'accepted'
        db.session.commit()
        flash('Wydarzenie zostało zaakceptowane.', category='success')
    elif action == 'reject':
        event.status = 'rejected'
        db.session.commit()
        flash('Wydarzenie zostało odrzucone.', category='warning')

    return redirect(url_for('views.admin_events'))

@views.route('/admin-users', methods=['GET', 'POST'])
@login_required
def admin_users():
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Nie masz uprawnień administratora do tej strony.', category='danger')
        return redirect(url_for('views.home'))
    
    pending_users = User.query.filter_by(status='pending').all()
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')  
        
        if action == 'accept':
            user = User.query.get(user_id)
            user.status = 'accepted'
            db.session.add(user)
            db.session.commit()
            flash('Stworzenie konta zostało zatwierdzone.', category='success')
        elif action == 'reject':
            user = User.query.get(user_id)
            user.status = 'rejected'
            flash('Stworzenie konta zostało odrzucone.', category='warning')
        
        return redirect(url_for('views.admin_users'))

    return render_template('admin_users.html', user=current_user, pending_users=pending_users)

@views.route("/report", methods=['GET', 'POST'])
@login_required
def report():
    user_reports = list(reversed(current_user.Reports))
    if request.method == 'POST':
        data = request.form.get('data')
        place = request.form.get('place')
        date = datetime.datetime.now()
            
        new_report = Report(data=data, date=date, place=place, user_id=current_user.id, status='pending')
        db.session.add(new_report) 
        db.session.commit()  
        flash('Wydarzenie zawnioskowano!', category='success')
            
            
        return redirect(url_for('views.report'))  
    
    return render_template('report.html', user=current_user,user_reports=user_reports)

@views.route('/update_user_status/<int:user_id>/<string:action>', methods=['POST'])
@login_required
def update_user_status(user_id, action):
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Nie masz uprawnień administratora do tej akcji.', category='danger')
        return redirect(url_for('views.admin_users'))

    user = User.query.get(user_id)
    if not user:
        flash('Nie znaleziono użytkownika.', category='danger')
        return redirect(url_for('views.admin_users'))

    if action == 'accept':
        user.status = 'accepted'
        db.session.commit()
        flash('Użytkownik został zaakceptowany.', category='success')
    elif action == 'reject':
        user.status = 'rejected'
        db.session.commit()
        flash('Użytkownik został odrzucony.', category='warning')

    return redirect(url_for('views.admin_users'))

@views.route('/update_report_status/<int:report_id>/<string:action>', methods=['POST'])
@login_required
def update_report_status(report_id, action):
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Nie masz uprawnień administratora do tej akcji.', category='danger')
        return redirect(url_for('views.admin_reports'))

    report = Report.query.get(report_id)
    if not report:
        flash('Nie znaleziono zgłoszenia.', category='danger')
        return redirect(url_for('views.admin_reports'))

    if action == 'accept':
        report.status = 'accepted'
        db.session.commit()
        flash('Zgłoszenie zostało zaakceptowane.', category='success')
    elif action == 'reject':
        report.status = 'rejected'
        db.session.commit()
        flash('Zgłoszenie zostało odmówione.', category='warning')

    return redirect(url_for('views.admin_reports'))

@views.route('/admin-reports', methods=['GET', 'POST'])
@login_required
def admin_reports():
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Nie masz uprawnień administratora do tej strony.', category='danger')
        return redirect(url_for('views.home'))
    
    pending_reports = Report.query.filter_by(status='pending').all()
    
    if request.method == 'POST':
        report_id = request.form.get('report_id')
        action = request.form.get('action')  
        
        if action == 'accept':
            event = Event.query.get(report_id)
            event.status = 'accepted'
            db.session.add(event)
            db.session.commit()
            flash('Zgłoszenie zostało zaakceptowane.', category='success')
        elif action == 'reject':
            event = Event.query.get(report_id)
            event.status = 'rejected'
            flash('Zgłoszenie zostało odmówione.', category='warning')
        
        return redirect(url_for('views.admin_reports'))

    return render_template('admin_reports.html',user=current_user, pending_reports=pending_reports)


stripe.api_key = 'sk_test_51P9F8mAHsD0ooQchiY1nEJu6Q5jpeRG1lvI8JqL0eHXuLbjDdgsZR9ai5TDU6h7qWcBk0EvKWTaWY02K4AIRoB9m00oxqHLQ4m'


@views.route('/payment', methods=['GET'])
def payment():
    return render_template('checkout.html')


@views.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'pln',
                        'product_data': {
                            'name': 'Rachunek za prąd',
                        },
                        'unit_amount': 9000,
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url='http://localhost:5000/success',
            cancel_url='http://localhost:5000/cancel',
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return str(e)


@views.route('/success')
def success():
    return render_template('sucess.html')


@views.route('/cancel')
def cancel():
    return render_template('cancel.html')

@views.route('/surveys', methods=['GET'])
@login_required
def surveys():
    surveys = Survey.query.filter_by(status='active').all()
    return render_template('surveys.html', surveys=surveys,user=current_user)

@views.route('/survey/<int:survey_id>', methods=['GET', 'POST'])
@login_required
def fill_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    if request.method == 'POST':
        for question in survey.questions:
            answer_text = request.form.get(f'question_{question.id}')
            answer = Answer(text=answer_text, question_id=question.id, user_id=current_user.id)
            db.session.add(answer)
        db.session.commit()
        survey.status = "completed"
        db.session.add(survey)
        db.session.commit()
        flash('Dziękujemy za wypełnienie ankiety!', 'success')
        return redirect(url_for('views.surveys'))
    return render_template('survey.html', survey=survey, user=current_user)

@views.route('/create-survey', methods=['GET', 'POST'])
@login_required
def create_survey():
    if request.method == 'POST':
        title = request.form.get('title')
        survey = Survey(title=title)
        questions = request.form.getlist('questions[]')
        db.session.add(survey)
        db.session.commit()
        for question_text in questions:
            if question_text.strip():  
                question = Question(text=question_text, survey_id=survey.id)
                db.session.add(question)

        db.session.commit()  
        flash('Ankieta została utworzona!', 'success')
        return redirect(url_for('views.create_survey'))
    return render_template('create_survey.html',user=current_user)