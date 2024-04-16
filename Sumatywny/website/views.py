from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Event
from . import db
import json
import calendar
import datetime

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST': 
        note = request.form.get('note')

        if len(note) < 1:
            flash('Event name is too short!', category='error') 
        else:
            new_note = Event(data=note, user_id=current_user.id) 
            db.session.add(new_note)
            db.session.commit()
            flash('Event added!', category='success')

    return render_template("home.html", user=current_user)


@views.route('/delete-note', methods=['POST'])
def delete_note():  
    event = json.loads(request.data)
    eventId = event['noteId']
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