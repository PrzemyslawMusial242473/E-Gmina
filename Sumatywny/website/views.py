import requests
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Event, MapMarker, User, Message
from . import db
import json
import calendar
import datetime

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


@views.route('/', methods=['GET', 'POST'])
def home():
    today = datetime.date.today()
    current_month = today.strftime("%B")
    year = today.year
    month = today.month
    month_events = get_month_events(year, month)
    accepted_month_events = [event for event in month_events if event.status == 'accepted']
    weeks = generate_calendar(year, month, accepted_month_events)
    accepted_events = Event.query.filter_by(status='accepted').all()
    markers = MapMarker.query.all()  # Pobieramy wszystkie znaczniki z bazy danych
    return render_template("home.html", calendar=weeks, current_month=current_month, user=current_user,
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
        flash('Znacznik nie znaleziony', category='error')
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
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            if user == current_user:
                flash('Nie możesz dodać samego siebie jako znajomego!', category='error')
            else:
                if user in current_user.friends:
                    flash(f'{user.email} jest już twoim znajomym!', category='error')
                elif user in current_user.sent:
                    flash(f'Zaproszenie wysłano do {user.email}!', category='error')
                elif user in current_user.invitations:
                    flash(f'Zaproszenie otrzymane od {user.email}!', category='error')
                else:
                    current_user.sent.append(user)
                    user.invitations.append(current_user)
                    db.session.commit()
                    flash(f'Zaproszenie pomyślnie wysłano do {user.email}!', category='success')
        else:
            flash('Użytkownik nie znaleziony!', category='error')
        return redirect(url_for('views.search_user'))
    return render_template('invite-friends.html', user=current_user)


@views.route('/accept-invite', methods=['POST'])
@login_required
def accept_invite():
    data = json.loads(request.data)
    inviter_email = data['inviter_email']
    inviter = User.query.filter_by(email=inviter_email).first()
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
    inviter = User.query.filter_by(email=inviter_email).first()
    if inviter in current_user.invitations:
        current_user.invitations.remove(inviter)
        inviter.sent.remove(current_user)
        db.session.commit()
    return jsonify({})


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


@views.route('/chat/<int:user_id>', methods=['GET'])
@login_required
def user_chat(user_id):
    receiver = User.query.get(user_id)
    if not receiver:
        flash('Nie znaleziono użytkownika.', category='error')
        return redirect(url_for('views.home'))

    messages_sent_by_user = Message.query.filter_by(sender_id=current_user.id, receiver_id=user_id).all()
    messages_received_by_user = Message.query.filter_by(sender_id=user_id, receiver_id=current_user.id).all()
    messages = messages_sent_by_user + messages_received_by_user
    messages.sort(key=lambda x: x.timestamp)

    return render_template('user_chat.html', user=current_user, receiver=receiver, messages=messages)


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
