from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Event
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
    year = today.year
    month = today.month
    cal = calendar.monthcalendar(year, month)
    weeks = []
    for week in cal:
        current_week = []
        for day in week:
            if day == 0:
                current_week.append("")
            else:
                current_week.append(day)
        weeks.append(current_week)
    return render_template("calendar.html", user=current_user, calendar=weeks)

@views.route('/maps', methods=['GET'])
def maps():
    # Pobierz dane dotyczące koszy na śmieci
    trash_bins = [
        {"lat": 37.7749, "lng": -122.4194},
        {"lat": 40.7128, "lng": -74.0060},
        {"lat": 34.0522, "lng": -118.2437}
    ]
    return render_template("maps.html", user=current_user, trash_bins=trash_bins)  # Przekazujemy dane do szablonu

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
