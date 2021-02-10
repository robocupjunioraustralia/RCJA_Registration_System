from common.baseTests import createStates
from django.test import TestCase
from django.core.exceptions import ValidationError

from users.models import User
from schools.models import School


class TestRegionClean(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)

    def testValidNoState(self):
        School.objects.create(name='New School', abbreviation='new', state=self.state2, region=self.region2_state1)
        User.objects.create(email='test@test.com', homeState=self.state2, homeRegion=self.region2_state1)

        self.assertEqual(self.region1.clean(), None)

    def testValidState(self):
        self.assertEqual(self.region2_state1.state, self.state1)
        self.assertEqual(self.region2_state1.clean(), None)

    def testInvalidStateUser(self):
        User.objects.create(email='test@test.com', homeState=self.state2, homeRegion=self.region2_state1)

        self.assertEqual(self.region2_state1.state, self.state1)
        self.assertRaises(ValidationError, self.region2_state1.clean)

    def testInvalidStateSchool(self):
        School.objects.create(name='New School', abbreviation='new', state=self.state2, region=self.region2_state1)

        self.assertEqual(self.region2_state1.state, self.state1)
        self.assertRaises(ValidationError, self.region2_state1.clean)

class TestRegionMethods(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)

    def testGetStateNone(self):
        self.assertEqual(None, self.region1.getState())

    def testGetState(self):
        self.assertEqual(self.state1, self.region2_state1.getState())

    def testStr(self):
        self.assertEqual('Region 1', str(self.region1))
