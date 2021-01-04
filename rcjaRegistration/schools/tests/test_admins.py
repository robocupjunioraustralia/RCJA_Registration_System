from common.baseTests.admin_permissions import Base_Test_NotStaff, Base_Test_SuperUser, Base_Test_FullCoordinator, Base_Test_ViewCoordinator

from django.test import TestCase


from common.baseTests.populateDatabase import createStates, createUsers, createSchools

class Schools_Base:
    modelURLName = 'schools_school'
    state1Obj = 'school1_state1'
    state2Obj = 'school3_state2'

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

