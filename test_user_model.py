"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///warbler-test'
app.config['SQLALCHEMY_ECHO'] = False
app.config['TESTING'] = True

db.create_all()

class UserModelTestCase(TestCase):
    """Test views for user."""

    def setUp(self):
        """Create test client, add sample data."""
        # db.drop_all()
        # db.create_all()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any database transactions"""
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

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

    def test_user_is_following(self):
        """Test user function 'is_following'."""

        [user1, user2] = seed() 

        self.assertEqual(user2.is_following(user1), True)
        self.assertEqual(user1.is_following(user2), False)
    
    def test_user_is_followed_by(self):
        """Test user function 'is_followed_by'."""

        [user1, user2] = seed()

        self.assertEqual(user2.is_followed_by(user1), False)
        self.assertEqual(user1.is_followed_by(user2), True)

    def test_user_signup(self):
        """Test user signup. Fail if duplicate usernames or emails."""

        user = User.signup(
        email="test1@test.com",
        username="testuser1",
        password="HASHED_PASSWORD",
        image_url="/static/images/default-pic.png"
        )

        self.assertIsInstance(user, User)

        # Raises IntegrityError to create user with same email   
        self.assertRaises(IntegrityError, User.signup,
            email="test1@test.com",
            username="testuser2",
            password="HASHED_PASSWORD",
            image_url="/static/images/default-pic.png"
            )

        db.session.rollback()

        # Raise IntegrityError to create user with same username
        self.assertRaises(IntegrityError, User.signup,
            email="test2@test.com",
            username="testuser1",
            password="HASHED_PASSWORD",
            image_url="/static/images/default-pic.png"
            )

    def test_user_authenicate(self):
        """Test user authenicate. Fail if username or password is incorrect"""

        seed()

        self.assertIsInstance(User.authenticate("testuser1","HASHED_PASSWORD"), User)

        # False when wrong password for username
        self.assertFalse(User.authenticate("testuser1","WRONG_PASSWORD"))

        # False when username doesnt exist
        self.assertFalse(User.authenticate("testuser","HASHED_PASSWORD"))


##############################################################
#
# Seed for tests
#
#
def seed():
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