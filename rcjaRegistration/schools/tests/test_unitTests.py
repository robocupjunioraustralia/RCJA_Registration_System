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
            state=None,
            region=None,
        )

        try:
            school.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testStateNoRegionValid(self):
        # State and region are required fields but not handled by clean
        school = School(
            name='New School',
            state=self.state1,
            region=None,
        )

        try:
            school.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testNoStateGlobalRegionValid(self):
        # State and region are required fields but not handled by clean
        school = School(
            name='New School',
            state=None,
            region=self.region1,
        )

        try:
            school.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testStateGlobalRegionValid(self):
        school = School(
            name='New School',
            state=self.state1,
            region=self.region1,
        )

        try:
            school.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testCorrectStateRegionValid(self):
        school = School(
            name='New School',
            state=self.state1,
            region=self.region2_state1,
        )

        try:
            school.clean()
        except ValidationError:
            self.fail('ValidationError raised unexpectedly')

    def testIncorrectStateRegionInvalid(self):
        school = School(
            name='New School',
            state=self.state2,
            region=self.region2_state1,
        )

        self.assertRaises(ValidationError, school.clean)

    def testNoStateRegionInvalid(self):
        # State and region are required fields but not handled by clean
        school = School(
            name='New School',
            state=None,
            region=self.region2_state1,
        )

        self.assertRaises(ValidationError, school.clean)
