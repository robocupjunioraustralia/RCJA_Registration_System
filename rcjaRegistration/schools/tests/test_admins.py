from common.baseTests.admin_permissions import Base_Test_NotStaff, Base_Test_SuperUser, Base_Test_FullCoordinator, Base_Test_ViewCoordinator

from django.test import TestCase


from common.baseTests.populateDatabase import createStates, createUsers, createSchools

class Schools_Base:
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

class Test_NotStaff(Schools_Base, Base_Test_NotStaff, TestCase):
    pass

class Test_SuperUser(Schools_Base, Base_Test_SuperUser, TestCase):
    expectedListItems = 4
    expectedStrings = [
        'School 1',
        'School 2',
        'School 3',
        'School 4',
    ]
    expectedMissingStrings = []

class Schools_Coordinators_Base(Schools_Base):
    expectedListItems = 2
    expectedStrings = [
        'School 1',
        'School 2',
    ]
    expectedMissingStrings = [
        'School 3',
        'School 4',
    ]

class Test_FullCoordinator(Schools_Coordinators_Base, Base_Test_FullCoordinator, TestCase):
    pass

class Test_ViewCoordinator(Schools_Coordinators_Base, Base_Test_ViewCoordinator, TestCase):
    pass

