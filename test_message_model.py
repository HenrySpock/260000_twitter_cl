"""Message model tests."""

# run these tests like:
#
# python -m unittest test_message_model.py 
# or
# python -m unittest -v test_message_model.py

import os
from unittest import TestCase
from models import db, User, Message, Follows
from app import app

# Set up test database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///warblerdb_test'
app.config['SQLALCHEMY_ECHO'] = False
app.config['TESTING'] = True

with app.app_context():
    db.drop_all()
    db.create_all()

class MessageModelTestCase(TestCase):
    def setUp(self):
        """Create test app, test client, and test data"""

        # Create database tables
        with app.app_context():
            db.drop_all()
            db.create_all()

            # Create test client
            self.client = app.test_client()

            # Create test data
            u1 = User(username='user1', email='user1@example.com', password='password')
            u2 = User(username='user2', email='user2@example.com', password='password')
            db.session.add_all([u1, u2])
            db.session.commit()
            m1 = Message(text='text message 1', user_id=u1.id)
            m2 = Message(text='text message 2', user_id=u2.id)
            db.session.add_all([m1, m2])
            db.session.commit()

    def test_message_model(self):
        """Does basic model work?"""

        # Retrieve test data
        with app.app_context():
            m1 = Message.query.filter_by(text='text message 1').one()
            m2 = Message.query.filter_by(text='text message 2').one()

            # Verify message contents
            self.assertEqual(m1.text, 'text message 1')
            self.assertEqual(m1.user_id, 1)
            self.assertEqual(m2.text, 'text message 2')
            self.assertEqual(m2.user_id, 2)

    def test_add_message(self):
        """Can a new message be added to the database?"""

        with app.app_context():
            u = User.query.filter_by(username='user1').one()
            message = Message(text='new message', user=u)
            db.session.add(message)
            db.session.commit()

            messages = Message.query.all()
            self.assertEqual(len(messages), 3)
            self.assertEqual(messages[2].text, 'new message')
            self.assertEqual(messages[2].user_id, u.id)
            
    def test_delete_message(self):
        """Can a message be deleted from the database?"""

        with app.app_context():
            message = Message.query.filter_by(text='text message 1').one()
            db.session.delete(message)
            db.session.commit()

            messages = Message.query.all()
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0].text, 'text message 2')          

    def test_message_user_relationship(self):
        """Does the user-Message relationship work?"""

        with app.app_context():
            u = User.query.filter_by(username='user1').one()
            message = Message(text='new message', user=u)
            db.session.add(message)
            db.session.commit()

            messages = u.messages
            self.assertEqual(len(messages), 2)
            self.assertEqual(messages[1].text, 'new message')    
            
    def tearDown(self):
        """Remove test data and database tables"""

        with app.app_context():
            db.session.rollback()
            User.query.delete()
            db.session.commit()  