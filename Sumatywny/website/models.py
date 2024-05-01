from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

friends = db.Table(
    'friends',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

invitations = db.Table(
    'invitations',
    db.Column('inviter_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('invitee_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

sent = db.Table(
    'sent',
    db.Column('sender_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('receiver_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    place = db.Column(db.String(150))
    name = db.Column(db.String(150))
    status = db.Column(db.String(50), default='pending')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    name = db.Column(db.String(150))
    surname = db.Column(db.String(150))
    address = db.Column(db.String(150))
    uid = db.Column(db.Integer, unique=True)
    role = db.Column(db.String(50), default='user')
    Events = db.relationship('Event')
    friends = db.relationship(
        'User',
        secondary=friends,
        primaryjoin=(friends.c.user_id == id),
        secondaryjoin=(friends.c.friend_id == id),
        backref=db.backref('friend_of', lazy='dynamic'),
        lazy='dynamic'
    )
    invitations = db.relationship(
        'User',
        secondary=invitations,
        primaryjoin=(invitations.c.invitee_id == id),
        secondaryjoin=(invitations.c.inviter_id == id),
        backref=db.backref('invited_by', lazy='dynamic'),
        lazy='dynamic'
    )
    sent = db.relationship(
        'User',
        secondary=sent,
        primaryjoin=(sent.c.sender_id == id),
        secondaryjoin=(sent.c.receiver_id == id),
        backref=db.backref('sent_by', lazy='dynamic'),
        lazy='dynamic'
    )


class MapMarker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    address = db.Column(db.String(255))
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))