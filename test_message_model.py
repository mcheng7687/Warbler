"""Message model tests."""

import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

app.config['SQLALCHEMY_ECHO'] = False
app.config['TESTING'] = True

db.create_all()

class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
            """Create test client, add sample data."""
            User.query.delete()
            Message.query.delete()
            Follows.query.delete()

            self.client = app.test_client()

    def tearDown(self):
        """Clean up any database transactions"""
        db.session.rollback()

    def test_message_model(self):
        """Does message class work?"""

        [user1, user2] = seedUsers()

        msg = seedMessage(user1)
        
        self.assertIsInstance(msg, Message)

    def test_message_cascade(self):
        """When user is deleted, all messages associated with the user is removed"""

        [user1, user2] = seedUsers()

        seedMessage(user1)
        seedMessage(user2)

        db.session.delete(user1)
        db.session.commit()

        self.assertEqual(Message.query.filter(Message.user_id==user1.id).all(), [])


##############################################################
#
# Seed for tests
#
#
def seedUsers():
    user1 = User.signup(
        email="test1@test.com",
        username="testuser1",
        password="HASHED_PASSWORD",
        image_url="/static/images/default-pic.png"
    )
    user2 = User.signup(
        email="test2@test.com",
        username="testuser2",
        password="HASHED_PASSWORD",
        image_url="/static/images/default-pic.png"
    )

    u2_follows_u1 = Follows(user_being_followed_id=user1.id, user_following_id=user2.id)

    db.session.add(u2_follows_u1)
    db.session.commit() 

    return [user1, user2]

def seedMessage(user):
    message = Message(text="This works!", user_id=user.id)

    db.session.add(message)
    db.session.commit()

    return message