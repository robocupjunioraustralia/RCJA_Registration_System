from common.baseTests import createStates
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.models import Q

from regions.utils import getRegionsLookup
from regions.models import State, Region

from users.models import User
from schools.models import School


class TestRegionClean(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)

    def testValidNoState(self):
        School.objects.create(name='New School', state=self.state2, region=self.region2_state1)
        User.objects.create(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email='test@test.com', homeState=self.state2, homeRegion=self.region2_state1)

        self.assertEqual(self.region1.clean(), None)

    def testValidState(self):
        self.assertEqual(self.region2_state1.state, self.state1)
        self.assertEqual(self.region2_state1.clean(), None)

    def testInvalidStateUser(self):
        User.objects.create(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email='test@test.com', homeState=self.state2, homeRegion=self.region2_state1)

        self.assertEqual(self.region2_state1.state, self.state1)
        self.assertRaises(ValidationError, self.region2_state1.clean)

    def testInvalidStateSchool(self):
        School.objects.create(name='New School', state=self.state2, region=self.region2_state1)

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

class TestGetRegionsLookup(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)

    def testLookupLength(self):
        self.state1.typeUserRegistration = False
        self.state1.save()

        lookup = getRegionsLookup()

        self.assertEqual(State.objects.filter(typeUserRegistration=True).count() + 1, len(lookup))

    def testRegistrationIn(self):
        lookup = getRegionsLookup()

        self.assertIn(self.state1.id, [x.id for x in lookup])

    def testNotUserRegistrationNotIn(self):
        self.state1.typeUserRegistration = False
        self.state1.save()

        lookup = getRegionsLookup()

        self.assertNotIn(self.state1.id, [x.id for x in lookup])

    def testBlankIn(self):
        lookup = getRegionsLookup()

        self.assertIn('', [x.id for x in lookup])

    def testStateContent(self):
        lookup = getRegionsLookup()

        self.assertEqual(2, lookup[1].regions.count())

    def testBlankContent(self):
        lookup = getRegionsLookup()

        self.assertEqual(1, lookup[0].regions.count())
