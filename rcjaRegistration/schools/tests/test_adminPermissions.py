from common.baseTests.adminPermissions import Base_Test_NotStaff, Base_Test_SuperUser, Base_Test_FullCoordinator, Base_Test_ViewCoordinator

from django.test import TestCase
from django.urls import reverse

# School

class School_Base:
    modelURLName = 'schools_school'
    state1Obj = 'school1_state1'
    state2Obj = 'school3_state2'
    validPayload = {
        'name': 'School 5',
        'abbreviation': 'SCH5',
        'state': 0,
        'region': 0,
        'campus_set-TOTAL_FORMS': 0,
        'campus_set-INITIAL_FORMS': 0,
        'campus_set-MIN_NUM_FORMS': 0,
        'campus_set-MAX_NUM_FORMS': 1000,
        'schooladministrator_set-TOTAL_FORMS': 0,
        'schooladministrator_set-INITIAL_FORMS': 0,
        'schooladministrator_set-MIN_NUM_FORMS': 0,
        'schooladministrator_set-MAX_NUM_FORMS': 1000,
    }

    def updatePayload(self):
        self.validPayload['state'] = self.state1.id
        self.validPayload['region'] = self.region1.id

class Test_School_NotStaff(School_Base, Base_Test_NotStaff, TestCase):
    pass

class Test_School_SuperUser(School_Base, Base_Test_SuperUser, TestCase):
    expectedListItems = 4
    expectedStrings = [
        'School 1',
        'School 2',
        'School 3',
        'School 4',
    ]
    expectedMissingStrings = []

    def testPostAddBlankState(self):
        payload = self.validPayload.copy()
        del payload['state']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'This field is required.')

class School_Coordinators_Base(School_Base):
    expectedListItems = 2
    expectedStrings = [
        'School 1',
        'School 2',
    ]
    expectedMissingStrings = [
        'School 3',
        'School 4',
    ]

class Test_School_FullCoordinator(School_Coordinators_Base, Base_Test_FullCoordinator, TestCase):
    def testPostAddBlankState(self):
        payload = self.validPayload.copy()
        del payload['state']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'This field is required.')

    def testPostAddWrongState(self):
        payload = self.validPayload.copy()
        payload['state'] = self.state2.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

class Test_School_ViewCoordinator(School_Coordinators_Base, Base_Test_ViewCoordinator, TestCase):
    pass

# School Administrator

class SchoolAdministrator_Base:
    modelURLName = 'schools_schooladministrator'
    state1Obj = 'schooladmin_mentor1'
    state2Obj = 'schooladmin_mentor4'
    validPayload = {
        'user': 0,
        'school': 0,
    }

    def updatePayload(self):
        self.validPayload['user'] = self.user_state2_school3_mentor4.id # Can edit users from any state, is only the school field that is filtered
        self.validPayload['school'] = self.school1_state1.id

class Test_SchoolAdministrator_NotStaff(SchoolAdministrator_Base, Base_Test_NotStaff, TestCase):
    pass

class Test_SchoolAdministrator_SuperUser(SchoolAdministrator_Base, Base_Test_SuperUser, TestCase):
    expectedListItems = 4
    expectedStrings = [
        'School 1',
        'School 2',
        'School 3',
    ]
    expectedMissingStrings = []

    def testPostAddBlankSchool(self):
        payload = self.validPayload.copy()
        del payload['school']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the errors below.') # Multiple errors because of checkRequiredFieldsNotNone validation
        self.assertContains(response, 'This field is required.')

class SchoolAdministrator_Coordinators_Base(SchoolAdministrator_Base):
    expectedListItems = 3
    expectedStrings = [
        'School 1',
        'School 2',
    ]
    expectedMissingStrings = [
        'School 3',
    ]

class Test_SchoolAdministrator_FullCoordinator(SchoolAdministrator_Coordinators_Base, Base_Test_FullCoordinator, TestCase):
    def testPostAddBlankSchool(self):
        payload = self.validPayload.copy()
        del payload['school']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the errors below.') # Multiple errors because of checkRequiredFieldsNotNone validation
        self.assertContains(response, 'This field is required.')

    def testPostAddSchoolWrongState(self):
        payload = self.validPayload.copy()
        payload['school'] = self.school4_state2.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the errors below.') # Multiple errors because of checkRequiredFieldsNotNone validation
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

class Test_SchoolAdministrator_ViewCoordinator(SchoolAdministrator_Coordinators_Base, Base_Test_ViewCoordinator, TestCase):
    pass
