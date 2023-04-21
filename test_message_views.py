"""Message View tests."""

# run these tests like:
#
# export FLASK_DEBUG=1
# python -m unittest -v test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warblerdb_test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

with app.app_context():
    db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            User.query.delete()
            Message.query.delete()

            self.client = app.test_client()

            self.testuser = User.signup(username="testuser",
                                        email="test@test.com",
                                        password="testuser",
                                        image_url=None)
            db.session.add(self.testuser)
            db.session.commit()
            
            user = User.query.filter_by(username="testuser").first()
            self.assertIsNotNone(user)
            self.assertEqual(user.username, "testuser")


    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
            self.assertEqual(msg.user_id, self.testuser.id)

    def test_show_message(self):
        """Can we show a message?"""

        # Create a test message
        with app.app_context():
            m = Message(
                id=1234,
                text="Test message",
                user_id=self.testuser.id
            )
            db.session.add(m)
            db.session.commit()


            with self.client as c:
                resp = c.get(f"/messages/{m.id}")
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn(m.text, html)

    def test_delete_message(self):
        """Can we delete a message?"""

        # Create a test message
        with app.app_context():
            m = Message(
                id=1234,
                text="Test message",
                user_id=self.testuser.id
            )
            db.session.add(m)
            db.session.commit()

            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id

                resp = c.post(f"/messages/{m.id}/delete")

                self.assertEqual(resp.status_code, 302)

                msg = Message.query.get(m.id)
                self.assertIsNone(msg)
             
    def tearDown(self): 
        with app.app_context():
            db.session.rollback()
            User.query.delete()
            db.session.commit() 