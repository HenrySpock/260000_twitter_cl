"""User model tests."""

# run these tests like:
#
# python -m unittest test_user_model.py 
# or
# python -m unittest -v test_user_model.py

import os
from unittest import TestCase
from models import db, User, Message, Follows
from app import app
from sqlalchemy import exc

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

# os.environ['DATABASE_URL'] = "postgresql:///warblerdb_test"
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///warblerdb_test'
app.config['SQLALCHEMY_ECHO'] = False

# Now we can import app



# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

# db.drop_all()
# db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        
        with app.app_context():
            db.drop_all()
            db.create_all() 
            User.query.delete()
            Message.query.delete()
            Follows.query.delete()

            self.client = app.test_client()
         
    def test_user_model(self):
        """Does basic model work?"""

        with app.app_context():
            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            ) 
            db.session.add(u)
            db.session.commit()

            # User should have no messages & no followers
            self.assertEqual(len(u.messages), 0)
            self.assertEqual(len(u.followers), 0)
    
    # Does the repr method work as expected?
    def test_user_repr(self):
        """Does __repr__ method work?"""

        with app.app_context():
            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )
            db.session.add(u)
            db.session.commit()

            self.assertEqual(
                repr(u),
                f"<User #{u.id}: {u.username}, {u.email}>"
            )
            
    # Does is_following successfully detect when user1 is following user2?
    # Does is_following successfully detect when user1 is not following user2?
    # Does is_followed_by successfully detect when user1 is followed by user2?
    # Does is_followed_by successfully detect when user1 is not followed by user2?

    def test_follows(self):
        """Does is_following and is_followed_by work?"""

        with app.app_context():
            # Create two users
            u1 = User(
                email="test1@test.com",
                username="testuser1",
                password="HASHED_PASSWORD1"
            )
            u2 = User(
                email="test2@test.com",
                username="testuser2",
                password="HASHED_PASSWORD2"
            )

            db.session.add_all([u1, u2])
            db.session.commit()

            # Initially, user1 is not following or followed by user2
            self.assertFalse(u1.is_following(u2))
            self.assertFalse(u1.is_followed_by(u2))

            # User1 follows user2
            u1.following.append(u2)
            db.session.commit()

            # Now, user1 is following user2
            self.assertTrue(u1.is_following(u2))
            self.assertFalse(u1.is_followed_by(u2))

            # User2 is followed by user1
            self.assertTrue(u2.is_followed_by(u1))
            self.assertFalse(u2.is_following(u1))

    # Does User.create successfully create a new user given valid credentials?
    # Does User.create fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?

    def test_create_user(self):
        """Does User.create successfully create a new user given valid credentials?"""

        with app.app_context():
            user = User.signup(
                username="testuser",
                email="test@test.com",
                password="password",
                image_url=None,
                header_image_url=None,
                bio=None,
                location=None
            )

            self.assertIsInstance(user, User)
            self.assertEqual(user.username, "testuser")
            self.assertEqual(user.email, "test@test.com")
            self.assertIsNotNone(user.password)

    def test_create_user_failure(self):
        """Does User.create fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?"""

        with app.app_context():
            # create a user with valid credentials
            user1 = User.signup(
                username="testuser",
                email="test@test.com",
                password="password",
                image_url=None,
                header_image_url=None,
                bio=None,
                location=None
            )

            db.session.add(user1)
            db.session.commit()

            # create another user with same username
            user2 = User.signup(
                username="testuser",
                email="test2@test.com",
                password="password",
                image_url=None,
                header_image_url=None,
                bio=None,
                location=None
            )

            with self.assertRaises(exc.IntegrityError) as context:
                db.session.add(user2)
                db.session.commit()
            self.assertIn('duplicate key value violates unique constraint "users_username_key"', str(context.exception))
            
    # Does User.authenticate successfully return a user when given a valid username and password?
    # Does User.authenticate fail to return a user when the username is invalid?
    # Does User.authenticate fail to return a user when the password is invalid?
    def test_authenticate_valid_credentials(self):
        """Does User.authenticate successfully return a user when given a valid username and password?"""

        with app.app_context():
            # create a user
            user = User.signup(
                username="testuser",
                email="test@test.com",
                password="password",
                image_url=None,
                header_image_url=None,
                bio=None,
                location=None
            )

            # authenticate with valid credentials
            authenticated_user = User.authenticate("testuser", "password")

            self.assertEqual(authenticated_user, user)

    def test_authenticate_invalid_username(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""

        with app.app_context():
            # create a user
            user = User.signup(
                username="testuser",
                email="test@test.com",
                password="password",
                image_url=None,
                header_image_url=None,
                bio=None,
                location=None
            )

            # authenticate with invalid username
            authenticated_user = User.authenticate("invalid_username", "password")

            self.assertFalse(authenticated_user)

    def test_authenticate_invalid_password(self):
        """Does User.authenticate fail to return a user when the password is invalid?"""

        with app.app_context():
            # create a user
            user = User.signup(
                username="testuser",
                email="test@test.com",
                password="password",
                image_url=None,
                header_image_url=None,
                bio=None,
                location=None
            )

            # authenticate with invalid password
            authenticated_user = User.authenticate("testuser", "invalid_password")

            self.assertFalse(authenticated_user)

    def tearDown(self): 
        with app.app_context():
            db.session.rollback()
            User.query.delete()
            db.session.commit() 

