from common.baseTests.adminPermissions import Base_Test_NotStaff, Base_Test_SuperUser, Base_Test_FullCoordinator, Base_Test_ViewCoordinator

from django.test import TestCase
from django.http import HttpRequest
from django.urls import reverse

# School

class State_Base:
    modelURLName = 'regions_state'
    state1Obj = 'state1'
    state2Obj = 'state2'
    validPayload = {
            'name': 'New State',
            'abbreviation': 'new',
        }

    def updatePayload(self):
        pass

class Test_State_NotStaff(State_Base, Base_Test_NotStaff, TestCase):
    pass

class Test_State_SuperUser(State_Base, Base_Test_SuperUser, TestCase):
    expectedListItems = 2
    expectedStrings = [
        'State 1',
        'State 2',
    ]
    expectedMissingStrings = []

class State_Coordinators_Base(State_Base):
    expectedListItems = 1
    expectedStrings = [
        'State 1',
    ]
    expectedMissingStrings = [
        'State 2',
    ]

class Test_State_FullCoordinator(State_Coordinators_Base, Base_Test_FullCoordinator, TestCase):
    pass

class Test_State_ViewCoordinator(State_Coordinators_Base, Base_Test_ViewCoordinator, TestCase):
    pass
