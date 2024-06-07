import unittest
from Sumatywny.website import create_app, db
from Sumatywny.website.views import get_month_events, generate_calendar
from Sumatywny.website.models import Event
from datetime import date


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
