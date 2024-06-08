from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import BLOB
import os
from datetime import datetime
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

class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(50), default='active')
    approved = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='surveys')
    questions = db.relationship('Question', backref='survey', lazy=True)

    def has_been_filled_by_user(self, user_id):
        return SurveyResponse.query.filter_by(survey_id=self.id, user_id=user_id).first() is not None



class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    answers = db.relationship('Answer', backref='question', lazy=True)


class SurveyResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    answers = db.relationship('Answer', backref='response', lazy=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    response_id = db.Column(db.Integer, db.ForeignKey('survey_response.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    place = db.Column(db.String(150))
    name = db.Column(db.String(150))
    status = db.Column(db.String(50), default='Oczekuje na rozpatrzenie')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='Events')


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
    loyalty_points = db.Column(db.Integer, default=0)
    front_document_image = db.Column(BLOB, nullable=True)
    back_document_image = db.Column(BLOB, nullable=True)
    Events = db.relationship('Event', back_populates='user')
    surveys = db.relationship('Survey', back_populates='user', lazy=True)
    Reports = db.relationship('Report')
    payments = db.relationship('Payment', backref='user', lazy=True)
    answers = db.relationship('Answer', backref='user', lazy=True)
    vouchers = db.relationship('Voucher', backref='user', lazy=True)
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
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])
    
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    place = db.Column(db.String(150))
    status = db.Column(db.String(50), default='pending')
    hidden = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
CATEGORIES = {
    "METALE I TWORZYWA SZTUCZNE": {
            "plastikowe butelki po napojach",
            "nakrętki",
            "plastikowe opakowania po produktach spożywczych",
            "opakowania wielomateriałowe",
            "opakowania po środkach czystości",
            "opakowania po kosmetykach",
            "plastikowe torby", 
            "worki", 
            "reklamówki",  
            "folie",
            "aluminiowe puszki po napojach i sokach",
            "puszki po konserwach",
            "folię aluminiową",
            "metale kolorowe",
            "kapsel", 
            "zakrętki od słoików"
        
    },
    "PAPIER": {   
            "opakowania z papieru",
            "karton",
            "tekturę",
            "katalogi", 
            "ulotki",
            "prospekty",
            "gazety i czasopisma",
            "papier szkolny i biurowy",
            "zadrukowane kartki",
            "zeszyty",
            "książki",
            "papier pakowy",
            "torby i worki papierowe"      
    },
    "SZKŁO": {
            "butelki i słoiki po napojach i żywności",
            "szklane opakowania po kosmetykach"
    
    },
    "ODPADY BIODEGRADOWALNE": {
            "odpadki warzywne i owocowe",
            "gałęzie drzew i krzewów",
            "skoszoną trawę",
            "liście",
            "kwiaty",
            "trociny i korę drzew",
            "niezaimpregnowane drewno",
            "resztki jedzenia"
        
    },
    "POZOSTAŁE":{
        "plastikowe zabawki",
        "opakowania po lekach i zużyte artykułów medyczne",
        "ręczniki papierowe",
        "zużyte chusteczki higieniczne",
        "opakowania po olejach silnikowych",
        "puszki i pojemniki po farbach i lakierach",
        "papier zatłuszczy lub mocno zabrudzony",
        "papierowe worki po nawozach, cemencie i innych materiałach budowlanych",
        "tapet",
        "pieluchy jednorazowe i inne materiałów higieniczne",
        "jednorazowe opakowania z papieru",
        "naczynia jednorazowe",
        "ubrania",
        "ceramika",
        "doniczki",
        "porcelana",
        "fajans",
        "kryształy",
        "szkło okularowe",
        "szkło żaroodporne",
        "znicz z zawartością wosku",
        "opakowania po rozpuszczalnikach", 
        "opakowania po olejach silnikowe",
        "lustro",
        "szyby okienne i/lub zbrojone",
        "kości zwierząt",
        "oleje jadalne",
        "odchody zwierząt",
        "popiół z węgla kamiennego",
        "drewno impregnowane",
        "płyty wiórowe i pilśniowe MDF",
        "ziemia",
        "kamienie"   
    },
    "SPECJALNE":{
        "części samochodowe",
        "zużyte baterie",
        "zużyte akumulatory",
        "zużyty sprzęt elektroniczny i/lub AGD",
        "żarówki",
        "świetlówki",
        "reflektory",
        "monitory",
        "lampy telewizyjne",
        "termometry",
        "strzykawki",
        "inne niebezpieczne odpady komunalne"    
    }
}
def segregate_waste(description):
    for category, items in CATEGORIES.items():
        if description in items:
            return f"{description} należy wyrzucać do: {category}"
    return f"Nie posiadamy '{description}' w bazie śmieci"

class Voucher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    store_name = db.Column(db.String(100))
    code = db.Column(db.String(100))
    creation_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    
stores = {
    'store1': {'name': 'Sklep spożywczy "U Moniki" -20%', 'cost': 10},
    'store2': {'name': 'Sklep odzieżowy "Dla Mamy&Córki" -30%', 'cost': 15},
    'store3': {'name': 'Księgarnia "Za Rogiem" -40%', 'cost': 20}
}
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_uid = db.Column(db.String(11), db.ForeignKey('user.uid'), nullable=False)  # Relacja z User
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    paid = db.Column(db.Boolean, default=False)

    def __init__(self, user_uid, amount, description, due_date):
        self.user_uid = user_uid
        self.amount = amount
        self.description = description
        self.due_date = due_date
        self.paid = False 


class Config:
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/document_images')
    
UPLOAD_FOLDER = 'website/templates/static/document_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}