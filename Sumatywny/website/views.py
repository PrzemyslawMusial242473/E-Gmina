import requests
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Event, MapMarker
from . import db
import json
import calendar
import datetime

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
def home():
    all_events = Event.query.all()
    return render_template("home.html", user=current_user,all_events = all_events)


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
    current_month = today.strftime("%B")  # Pobieranie nazwy aktualnego miesiąca
    year = today.year
    month = today.month
    cal = calendar.monthcalendar(year, month)

    # Pobieranie wydarzeń z bazy danych dla bieżącego miesiąca
    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month, calendar.monthrange(year, month)[1])
    month_events = Event.query.filter(Event.date.between(start_date, end_date)).all()

    # Tworzenie listy tygodni z wydarzeniami
    weeks = []
    for week in cal:
        current_week = []
        for day in week:
            events_for_day = [event for event in month_events if event.date.day == day]
            current_week.append((day, events_for_day))
        weeks.append(current_week)

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

            flash('Marker added successfully', category='success')
            return redirect(url_for('views.maps'))
        else:
            flash('Could not find coordinates for the provided address', category='error')
            return redirect(url_for('views.maps'))

    markers = MapMarker.query.all()  # Pobieramy wszystkie znaczniki z bazy danych
    return render_template("maps.html", user=current_user, markers=markers)

@views.route('/delete-marker/<int:marker_id>', methods=['POST'])
def delete_marker(marker_id):
    marker = MapMarker.query.get(marker_id)
    if marker:
        db.session.delete(marker)
        db.session.commit()
        flash('Marker deleted successfully', category='success')
    else:
        flash('Marker not found', category='error')
    return redirect(url_for('views.maps'))

@views.route('/events', methods=['GET', 'POST'])
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
                return 'Invalid date format'
            
            new_event = Event(data=data, date=date, place=place, name=name,user_id=current_user.id)
            
            db.session.add(new_event)
            db.session.commit()
            flash('Event added!', category='success')
            
            return redirect(url_for('views.home'))  
    
    return render_template('events.html', user=current_user,user_events=user_events)
