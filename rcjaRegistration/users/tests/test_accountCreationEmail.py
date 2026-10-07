from common.baseTests import createStates, createEvents, createUsers
from django.test import TestCase
from django.core.exceptions import ValidationError
from unittest.mock import patch, Mock
from django.urls import reverse
from django.test import Client
from django.http import HttpRequest

from schools.models import School, SchoolAdministrator
from regions.models import State, Region
from users.models import User
from coordination.models import Coordinator
from events.models import Year
from django.core import mail


class Test_LoginRequired(TestCase):
    email = "user@user.com"
    password = "chdj48958DJFHJGKDFNM"
    validPayload = {
        "email": email,
        "password": password,
        "passwordConfirm": password,
        "first_name": "first",
        "last_name": "last",
        "mobileNumber": "123123123",
        "homeState": 1,
        "homeRegion": 1,
    }

    def setUp(self):
        createStates(self)
        createUsers(self)
        createEvents(self)

        self.user = User.objects.create_user(
            adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION,
            email="admin@test.com",
            password="admin",
        )

        self.validPayload["homeState"] = self.state1.id
        self.validPayload["homeRegion"] = self.region2_state1.id

    def testDefaultEmail(self):
        payloadData = self.validPayload
        response = self.client.post(path=reverse("users:signup"), data=payloadData)
        self.assertEqual(1, len(mail.outbox))
        email = mail.outbox[0]
        self.assertEqual(email.from_email, "system@enter.robocupjunior.org.au")

        self.assertEqual(len(email.attachments), 0)
        self.assertEqual(len(email.recipients()), 1)
        self.assertEqual(email.recipients()[0], self.email)
        self.assertEqual(email.subject, "Welcome to Robocup")
        self.assertEqual(
            email.message()._payload,
            """Dear first last,
Welcome to Robocup Junior Austrailia. 
Looking forward to seeing you at our next competition.
The following competitions are occurring in State 1:
- State 1 Open Competition    8 Jul 2026
The following workshops are occurring in State 1:
- State 1 Open Workshop    26 Jun 2026
Warmest regards,
RCJA""",
        )

    def testNonDefaultEmail(self):
        self.state2.introductionEmailTemplate = (
            "The name is: {{name}}\nThe events are {{events}}\nCheers, RCJA"
        )
        self.state2.save()
        payloadData = self.validPayload
        payloadData["homeState"] = self.state2.id
        payloadData["homeRegion"] = self.region3_state2.id
        response = self.client.post(path=reverse("users:signup"), data=payloadData)
        self.assertEqual(1, len(mail.outbox))
        email = mail.outbox[0]
        self.assertEqual(email.from_email, "system@enter.robocupjunior.org.au")

        self.assertEqual(len(email.attachments), 0)
        self.assertEqual(len(email.recipients()), 1)
        self.assertEqual(email.recipients()[0], self.email)
        self.assertEqual(email.subject, "Welcome to Robocup")
        self.assertEqual(
            email.message()._payload,
            """The name is: first last
The events are The following competitions are occurring in State 2:
- State 2 Open Competition    13 Jul 2026
The following workshops are occurring in State 2:
- State 2 Open Workshop    26 Jun 2026
Cheers, RCJA""",
        )
