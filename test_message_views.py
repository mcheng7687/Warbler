"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

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

    def test_get_message(self):
        """Retrive message with message_id"""

        msg = seedMessage(self.testuser.id)

        with self.client as c:

            resp = c.get(f"/messages/{msg.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code,200)
            self.assertIn('<p class="single-message">This works!</p>\n', html)

    def test_delete_message_as_owner(self):
        """Delete message as message's user"""

        msg = seedMessage(self.testuser.id)
        msg_id = msg.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.post(f"/messages/{msg_id}/delete", follow_redirects = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIsNone(Message.query.get(msg_id))

    def test_delete_message_not_as_owner(self):
        """"Attempt to delete message as another user"""

        other_user = seedUser()
        msg = seedMessage(other_user.id)

        with self.client as c:
            
            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects = True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)
            
    def test_like_message(self):
        """Like messages of other users"""

        other_user = seedUser()
        msg = seedMessage(other_user.id)
        msg_id = msg.id
        seedFollow(self.testuser.id, other_user.id)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            # Add a like to seed message
            resp = c.post(f"/messages/{msg_id}/add_like", follow_redirects = True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<i class="fa fa-thumbs-up" style="color:mediumaquamarine"></i>', html)

            like = Likes.query.filter(Likes.user_id==self.testuser.id, Likes.message_id==msg_id).one()
            
            self.assertIsInstance(like, Likes)

            # Remove a like from seed message
            resp = c.post(f"/messages/{msg_id}/add_like", follow_redirects = True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<i class="fa fa-thumbs-up"></i>', html)

    def test_show_liked_mesages(self):
        """Show all liked messages."""

        other_user = seedUser()
        msg = seedMessage(other_user.id)
        seedLike(msg.id, self.testuser.id)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            resp = c.get("/messages/liked")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>This works!</p>', html)

    def test_remove_like(self):
        """Remove an existing 'like'."""

        other_user = seedUser()
        msg = seedMessage(other_user.id)
        msg_id = msg.id
        seedLike(msg_id, self.testuser.id)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/{msg_id}/remove_like", follow_redirects = True)
            # html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIsNone(Likes.query.filter(Likes.user_id==self.testuser.id, Likes.message_id==msg_id).one_or_none())



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