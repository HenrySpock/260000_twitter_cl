from app import app, CURR_USER_KEY
from unittest import TestCase
from models import db, connect_db, User, Message, Follows, Likes
from flask import session
from forms import UserEditForm

# run these tests like:
#
# export FLASK_DEBUG=1
# python -m unittest -v test_user_views.py

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///warblerdb_test'
app.config['SQLALCHEMY_ECHO'] = False

app.config['TESTING'] = True

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            db.drop_all()
            db.create_all()

            self.client = app.test_client()

            # create test user
            u = User.signup(username="testuser",
                            email="test@test.com",
                            password="testuser",
                            image_url=None)

            # create second test user
            u2 = User.signup(username="testuser2",
                            email="test2@test.com",
                            password="testuser2",
                            image_url=None)

            db.session.add_all([u, u2])
            db.session.commit()

            self.user_id = u.id
        
    def test_list_users(self):
        """Can we successfully retrieve a list of all users?"""
        with app.app_context():
            with self.client as c:
                resp = c.get("/users")
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("@testuser", html)
                self.assertIn("@testuser2", html)

    def test_users_show(self):
        """Can we successfully retrieve a user's profile page?"""
        with app.app_context():
            with self.client as c:
                resp = c.get(f"/users/{self.user_id}")
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("@testuser", html)

    def test_show_following(self):
        """Can we successfully retrieve a list of people this user is following?"""
        with app.app_context():
            with self.client as c:
                resp = c.get(f"/users/{self.user_id}/following", follow_redirects=True)
                self.assertEqual(resp.status_code, 200) 

    def test_users_followers(self):
        """Can we successfully retrieve a list of followers of this user?"""
        with app.app_context():
            with self.client as c:
                resp = c.get(f"/users/{self.user_id}/followers")
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 302) 

    def test_add_follow(self):
        """Can we successfully add a follow for the currently-logged-in user?"""
        with app.app_context():
            with self.client as c:
                # log in as testuser
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.user_id

                # follow testuser2
                resp = c.post(f"/users/follow/{self.user_id+1}")

                self.assertEqual(resp.status_code, 302)

                # check that the user is now following testuser2
                u = User.query.get(self.user_id)
                u2 = User.query.get(self.user_id+1)
                self.assertIn(u2, u.following)

    def test_user_edit_route(self):
        """Test user edit route."""
        with app.app_context():
            with app.test_client() as client:
                # create a new user
                user = User.signup(username="edituser",
                                    email="edit@test.com",
                                    password="password",
                                    image_url=None)
                db.session.add(user)
                db.session.commit()

                # log in the user
                client.post('/login', data={
                    'username': 'testuser',
                    'password': 'password'
                })

                # get the edit profile page
                resp = client.get(f'/users/{user.id}/edit')
                html = resp.get_data(as_text=True)

                # check that the response shows the user's current information
                self.assertIn("Edit Your Profile", html)
                self.assertIn(user.username, html)
                self.assertIn(user.email, html)

                # submit the edit profile form
                form = UserEditForm()
                form.username.data = "newusername"
                form.email.data = "newemail@test.com"
                form.password.data = "password"
                form.image_url.data = None
                form.header_image_url.data = None
                form.bio.data = None
                form.location.data = None

                resp = client.post(f'/users/{user.id}/edit', data=form.data)

                # check that the user's information has been updated in the database
                updated_user = User.query.filter_by(id=user.id).first()
                self.assertEqual(updated_user.username, "newusername")
                self.assertEqual(updated_user.email, "newemail@test.com")
        
    def test_delete_user(self):
        """Can user delete their own account?"""
        with app.app_context():
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.user_id

                resp = c.post(f"/users/delete", follow_redirects=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIsNone(User.query.get(self.user_id))
                        
    def tearDown(self): 
        with app.app_context():
            db.session.rollback()
            User.query.delete()
            db.session.commit() 