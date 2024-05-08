from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
import datetime

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

blocked = db.Table(
    'blocked',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('blocked_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

y_blocked = db.Table(
    'y_blocked',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('blocked_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
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
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    name = db.Column(db.String(150))
    surname = db.Column(db.String(150))
    address = db.Column(db.String(150))
    uid = db.Column(db.Integer, unique=True)
    status = db.Column(db.String(50), default='pending')
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
    blocked = db.relationship(
        'User',
        secondary=blocked,
        primaryjoin=(blocked.c.user_id == id),
        secondaryjoin=(blocked.c.blocked_id == id),
        backref=db.backref('blocked_by', lazy='dynamic'),
        lazy='dynamic'
    )
    y_blocked = db.relationship(
        'User',
        secondary=y_blocked,
        primaryjoin=(y_blocked.c.user_id == id),
        secondaryjoin=(y_blocked.c.blocked_id == id),
        backref=db.backref('y_blocked_by', lazy='dynamic'),
        lazy='dynamic'
    )


class MapMarker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    address = db.Column(db.String(255))
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])
