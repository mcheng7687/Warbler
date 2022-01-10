"""User View tests."""

import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for user."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

    def tearDown(self):
        """Clean up any database transactions"""
        db.session.rollback()

    def test_add_follow(self):
        """Add a following from logged in user"""

        other_user = seedUser()
        other_user_id = other_user.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/users/follow/{other_user_id}")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"http://localhost/users/{self.testuser.id}/following")

            follow = Follows.query.filter(Follows.user_being_followed_id==other_user.id, Follows.user_following_id==self.testuser.id).one_or_none()
            self.assertIsInstance(follow, Follows)

    def test_stop_following(self):
        """Remove a following"""

        other_user = seedUser()
        other_user_id = other_user.id
        seedFollow(self.testuser.id, other_user_id)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/users/stop-following/{other_user_id}")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"http://localhost/users/{self.testuser.id}/following")

            follow = Follows.query.filter(Follows.user_being_followed_id==other_user_id, Follows.user_following_id==self.testuser.id).one_or_none()
            self.assertIsNone(follow)

    def test_user_update_profile(self):
        """Update the profile of logged in user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/users/profile", data={'username':'anothertestuser', 
                                                'email':'anothertest@test.com', 
                                                'image_url':"None", 
                                                'header_image_url':"None", 
                                                'bio':'Here the test runs'})

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"http://localhost/users/{self.testuser.id}")

            user = User.query.get(self.testuser.id)
            self.assertEqual(user.username, "anothertestuser")
            self.assertEqual(user.email, "anothertest@test.com")
            self.assertEqual(user.bio, "Here the test runs")

    def test_another_user_update_profile(self):
        """Attempt to update the profile of user without logging in"""

        with self.client as c:

            resp = c.post("/users/profile", data={'username':'anothertestuser', 
                                                'email':'anothertest@test.com', 
                                                'image_url':"None", 
                                                'header_image_url':"None", 
                                                'bio':'Here the test runs'})
            
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"http://localhost/login")

    def test_delete_user(self):
        """Delete user of logged in user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/users/delete")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"http://localhost/signup")

            # Test if user got deleted. Should return None
            user = User.query.get(self.testuser.id)
            self.assertIsNone(user)

    def test_delete_another_user(self):
        """Attempt to delete user without logging in"""

        with self.client as c:

            resp = c.post("/users/delete")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"http://localhost/")

            # Test if user got deleted. Should return a User
            user = User.query.get(self.testuser.id)
            self.assertIsInstance(user, User)

##############################################################
#
# Seed for tests
#
#
def seedUser():
    user1 = User.signup(
        email="test1@test.com",
        username="testuser1",
        password="HASHED_PASSWORD",
        image_url="/static/images/default-pic.png"
    )
    
    return user1

def seedMessage(user_id):
    message = Message(text="This works!", user_id=user_id)

    db.session.add(message)
    db.session.commit()

    return message

def seedFollow(follower_id, following_id):
    follow = Follows(user_being_followed_id=following_id, user_following_id=follower_id)

    db.session.add(follow)
    db.session.commit()

def seedLike(message_id, user_id):

    like = Likes(user_id=user_id, message_id=message_id)

    db.session.add(like)
    db.session.commit()