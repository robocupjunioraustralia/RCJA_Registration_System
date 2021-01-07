from common.baseTests.adminPermissions import Base_Test_NotStaff, Base_Test_SuperUser, Base_Test_FullCoordinator, Base_Test_ViewCoordinator

from django.test import TestCase
from django.urls import reverse

from regions.models import State

# State

class State_Base:
    modelURLName = 'regions_state'
    state1Obj = 'state1'
    state2Obj = 'state2'
    validPayload = {
        'name': 'New State',
        'abbreviation': 'new',
        'coordinator_set-TOTAL_FORMS': 0,
        'coordinator_set-INITIAL_FORMS': 0,
        'coordinator_set-MIN_NUM_FORMS': 0,
        'coordinator_set-MAX_NUM_FORMS': 1000,
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

    expectedAddInlines = []
    expectedMissingAddInlines = ['Coordinators']
    expectedChangeInlines = ['Coordinators']
    expectedMissingChangeInlines = []

    expectedAddEditableFields = [
        ('typeRegistration', 'Registration'),
        ('typeGlobal', 'Global'),
        ('typeWebsite', 'Website'),
    ]
    expectedAddReadonlyFields = []
    # Existing states are typeRegistration=True
    expectedChangeEditableFields = [
        ('typeWebsite', 'Website'),
    ]
    expectedChangeReadonlyFields = [
        ('typeRegistration', 'Registration'),
        ('typeGlobal', 'Global'),
    ]

    # Additional readonly field tests

    def testCorrectReadonlyFields_changeNotRegistration(self):
        self.state3 = State.objects.create(name='State 3', abbreviation='ST3')

        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state3.id,)))

        self.assertNotContains(response, '<label>Registration:</label>')
        self.assertContains(response, '<input type="checkbox" name="typeRegistration"')

        self.assertNotContains(response, '<label>Global:</label>')
        self.assertContains(response, '<input type="checkbox" name="typeGlobal"')

        self.assertNotContains(response, '<label>Website:</label>')
        self.assertContains(response, '<input type="checkbox" name="typeWebsite"')

    def testCorrectReadonlyFields_changeGlobal(self):
        self.state3 = State.objects.create(name='State 3', abbreviation='ST3', typeGlobal=True)

        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state3.id,)))

        self.assertContains(response, '<label>Registration:</label>')
        self.assertNotContains(response, '<input type="checkbox" name="typeRegistration"')

        self.assertNotContains(response, '<label>Global:</label>')
        self.assertContains(response, '<input type="checkbox" name="typeGlobal"')

        self.assertNotContains(response, '<label>Website:</label>')
        self.assertContains(response, '<input type="checkbox" name="typeWebsite"')

    def testCorrectReadonlyFields_changeOtherGlobal(self):
        self.state3 = State.objects.create(name='State 3', abbreviation='ST3')
        self.state4 = State.objects.create(name='State 4', abbreviation='ST4', typeGlobal=True)

        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state3.id,)))

        self.assertNotContains(response, '<label>Registration:</label>')
        self.assertContains(response, '<input type="checkbox" name="typeRegistration"')

        self.assertContains(response, '<label>Global:</label>')
        self.assertNotContains(response, '<input type="checkbox" name="typeGlobal"')

        self.assertNotContains(response, '<label>Website:</label>')
        self.assertContains(response, '<input type="checkbox" name="typeWebsite"')

class State_Coordinators_Base(State_Base):
    expectedListItems = 1
    expectedStrings = [
        'State 1',
    ]
    expectedMissingStrings = [
        'State 2',
    ]

class Test_State_FullCoordinator(State_Coordinators_Base, Base_Test_FullCoordinator, TestCase):
    addLoadsCode = 403
    deleteLoadsCode = 403
    addPostCode = 403

    expectedChangeInlines = ['Coordinators']
    expectedMissingChangeInlines = []

    expectedChangeReadonlyFields = [
        ('typeRegistration', 'Registration'),
        ('typeGlobal', 'Global'),
        ('typeWebsite', 'Website'),
    ]

class Test_State_ViewCoordinator(State_Coordinators_Base, Base_Test_ViewCoordinator, TestCase):
    expectedChangeInlines = []
    expectedMissingChangeInlines = ['Coordinators']

    expectedChangeReadonlyFields = [
        ('typeRegistration', 'Registration'),
        ('typeGlobal', 'Global'),
        ('typeWebsite', 'Website'),
    ]
