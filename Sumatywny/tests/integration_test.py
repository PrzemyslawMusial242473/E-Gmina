import unittest
from Sumatywny.website import create_app, db
from Sumatywny.website.models import User, Survey, Question, SurveyResponse, Answer, Payment
from flask_login import login_user
from datetime import datetime
import io


class IntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.admin = User(username='admin', email='admin@example.com', password='password', role='admin')
        self.user = User(username='testuser', email='testuser@example.com', password='password', role='user')
        db.session.add_all([self.admin, self.user])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, username):
        with self.app.test_request_context():
            user = User.query.filter_by(username=username).first()
            login_user(user)

    def test_survey_submission(self):
        self.login('testuser')
        survey = Survey(title='Test Survey', user_id=self.admin.id, approved=True, status='active')
        db.session.add(survey)
        db.session.commit()

        question = Question(text='What is your favorite color?', survey_id=survey.id)
        db.session.add(question)
        db.session.commit()

        response = self.client.post(f'/survey/{survey.id}', data={'question_1': 'Blue'})
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            response = SurveyResponse.query.filter_by(survey_id=survey.id).first()
            self.assertIsNotNone(response)
            self.assertEqual(response.answers[0].text, 'Blue')

    def test_upload_payments(self):
        self.login('admin')
        data = {
            'file': (io.BytesIO(b"Email,Description,Amount,Due Date\n"
                                b"testuser@example.com,Test Payment,100.0,2024-06-30"), 'payments.xlsx')
        }
        response = self.client.post('/upload-payments', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 302)


if __name__ == '_main_':
    unittest.main()
