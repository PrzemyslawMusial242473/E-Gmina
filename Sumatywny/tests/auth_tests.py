import unittest

from Sumatywny.website import create_app, db
from Sumatywny.website.auth import hash_password, verify_password
from Sumatywny.website.models import User


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_hash_password(self):
        password = 'password123'
        hashed_password = hash_password(password)
        self.assertTrue(hashed_password)
        self.assertNotEqual(password, hashed_password)

    def test_verify_password(self):
        password = 'password123'
        hashed_password = hash_password(password)
        self.assertTrue(verify_password(hashed_password, password))
        self.assertFalse(verify_password(hashed_password, 'wrongpassword'))

    def test_login(self):
        # create a user
        user = User(email='test@example.com', password=hash_password('password123'))
        db.session.add(user)
        db.session.commit()

        # test login with correct credentials
        with self.app.test_client() as client:
            response = client.post('/login', data={'email': 'test@example.com', 'password': 'password123'},
                                   follow_redirects=True)
            self.assertEqual(response.status_code, 200)  # Success page after login

            # test login with incorrect credentials
            response = client.post('/login', data={'email': 'test@example.com', 'password': 'wrongpassword'},
                                   follow_redirects=True)
            self.assertIn(b'Twoje konto nie zosta\xc5\x82o jeszcze zatwierdzone',
                          response.data)  # Flash message displayed


if __name__ == '__main__':
    unittest.main()
