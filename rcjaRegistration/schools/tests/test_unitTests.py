from common.baseTests import createStates
from django.test import TestCase
from django.core.exceptions import ValidationError

from schools.models import School

class TestSchoolRegionFieldClean(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)

    def testNoStateNoRegionValid(self):
        # State and region are required fields but not handled by clean
        school = School(
            name='New School',
            abbreviation='new',
            state=None,
            region=None,
        )

        self.assertEqual(school.clean(), None)

    def testStateNoRegionValid(self):
        # State and region are required fields but not handled by clean
        school = School(
            name='New School',
            abbreviation='new',
            state=self.state1,
            region=None,
        )

        self.assertEqual(school.clean(), None)

    def testNoStateGlobalRegionValid(self):
        # State and region are required fields but not handled by clean
        school = School(
            name='New School',
            abbreviation='new',
            state=None,
            region=self.region1,
        )

        self.assertEqual(school.clean(), None)

    def testStateGlobalRegionValid(self):
        school = School(
            name='New School',
            abbreviation='new',
            state=self.state1,
            region=self.region1,
        )

        self.assertEqual(school.clean(), None)

    def testCorrectStateRegionValid(self):
        school = School(
            name='New School',
            abbreviation='new',
            state=self.state1,
            region=self.region2_state1,
        )

        self.assertEqual(school.clean(), None)

    def testIncorrectStateRegionInvalid(self):
        school = School(
            name='New School',
            abbreviation='new',
            state=self.state2,
            region=self.region2_state1,
        )

        self.assertRaises(ValidationError, school.clean)

    def testNoStateRegionInvalid(self):
        # State and region are required fields but not handled by clean
        school = School(
            name='New School',
            abbreviation='new',
            state=None,
            region=self.region2_state1,
        )

        self.assertRaises(ValidationError, school.clean)
