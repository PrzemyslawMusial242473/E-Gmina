import unittest
from Sumatywny.website import create_app, db
from Sumatywny.website.views import get_month_events, generate_calendar, User, Payment, Survey, Question, SurveyResponse, Answer
from Sumatywny.website.models import Event
from Sumatywny.website.auth import hash_password
from datetime import date
from flask_login import login_user
from datetime import datetime
import io


class TestViews(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_month_events(self):
        event1 = Event(data='Test Event 1', date=date(2024, 6, 1), status='Zaakceptowane')
        event2 = Event(data='Test Event 2', date=date(2024, 6, 15), status='Zaakceptowane')

        db.session.add_all([event1, event2])
        db.session.commit()

        month_events = get_month_events(2024, 6)
        self.assertEqual(len(month_events), 2)
        self.assertEqual(month_events[0].data, 'Test Event 1')

    def test_generate_calendar(self):
        month_events = [
            Event(data='Test Event 1', date=date(2024, 6, 1), status='Zaakceptowane'),
            Event(data='Test Event 2', date=date(2024, 6, 15), status='Zaakceptowane'),
        ]

        calendar = generate_calendar(2024, 6, month_events)

        self.assertEqual(len(calendar), 5)
        self.assertEqual(len(calendar[0]), 7)

    def test_home_route(self):
        with self.app.test_client() as client:
            response = client.get('/')
            self.assertEqual(response.status_code, 200)

    def test_maps_route(self):
        with self.app.test_client() as client:
            response = client.get('/maps')
            self.assertEqual(response.status_code, 200)


class PaymentTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, username):
        admin = User(username='admin', email='admin@example.com', password=hash_password('password'), role='admin',
                     status="accepted")
        user = User(username='testuser', email='testuser@example.com', password=hash_password('password'), uid=22222222222, role='user',
                    status="accepted")
        db.session.add_all([admin, user])
        db.session.commit()
        with self.app.test_request_context():
            user = User.query.filter_by(username=username).first()
            login_user(user)

    def test_upload_payments(self):
        self.login('admin')
        data = {
            'file': (io.BytesIO(b"Email,Description,Amount,Due Date\n"
                                b"testuser@example.com,Test Payment,100.0,2024-06-30"), 'payments.xlsx')
        }
        response = self.client.post('/upload-payments', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 302)

    def test_create_checkout_session(self):
        self.login('testuser')
        with self.app.app_context():
            user = User.query.filter_by(username='testuser').first()
            due_date = datetime.strptime('2024-06-30', '%Y-%m-%d')
            payment = Payment(user_uid=user.uid, description='Test Payment', amount=100.0, due_date=due_date)
            db.session.add(payment)
            db.session.commit()
            payment_id = payment.id

        response = self.client.post('/create-checkout-session', data={'payment_id': payment_id})
        self.assertEqual(response.status_code, 303)
        self.assertIn('stripe.com', response.location)

    def test_payments_view(self):
        self.login('testuser')
        with self.app.app_context():
            user = User.query.filter_by(username='testuser').first()
            due_date = datetime.strptime('2024-06-30', '%Y-%m-%d')
            payment = Payment(user_uid=user.uid, description='Test Payment', amount=100.0, due_date=due_date)
            db.session.add(payment)
            db.session.commit()

        response = self.client.get('/payments')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Payment', response.data.decode('utf-8'))


class SurveyTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


    def login(self, username):
        admin = User(username='admin', email='admin@example.com', password=hash_password('password'), role='admin',
                     status="accepted")
        user = User(username='testuser', email='testuser@example.com', password=hash_password('password'), uid=22222222222, role='user',
                    status="accepted")
        db.session.add_all([admin, user])
        db.session.commit()
        survey = Survey(title='Test Survey', user_id=admin.id, approved=True, status='active')
        db.session.add(survey)
        db.session.commit()

        question = Question(text='What is your favorite color?', survey_id=survey.id)
        db.session.add(question)
        db.session.commit()
        with self.app.test_request_context():
            user = User.query.filter_by(username=username).first()
            login_user(user)

    def test_survey_display(self):
        self.login('testuser')
        response = self.client.get('/surveys')
        self.assertEqual(response.status_code, 200)

    def test_fill_survey(self):
        self.login('testuser')
        survey = Survey.query.filter_by(title='Test Survey').first()
        response = self.client.post(f'/survey/{survey.id}', data={
            'question_1': 'Blue'
        })
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            response = SurveyResponse.query.filter_by(survey_id=survey.id).first()
            self.assertIsNotNone(response)
            self.assertEqual(response.answers[0].text, 'Blue')

    def test_survey_results(self):
        self.login('admin')
        with self.app.app_context():
            survey = Survey.query.filter_by(title='Test Survey').first()
            response = SurveyResponse(survey_id=survey.id, user_id=User.query.filter_by(username='testuser').first().id)
            db.session.add(response)
            db.session.commit()
            answer = Answer(text='Blue', question_id=survey.questions[0].id, response_id=response.id,
                            user_id=response.user_id)
            db.session.add(answer)
            db.session.commit()

        response = self.client.get('/survey_results')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Survey', response.data.decode('utf-8'))
        self.assertIn('Blue', response.data.decode('utf-8'))


if __name__ == '_main_':
    unittest.main()