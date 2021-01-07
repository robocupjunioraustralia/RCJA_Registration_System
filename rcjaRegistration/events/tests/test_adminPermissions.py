from common.baseTests.adminPermissions import Base_Test_NotStaff, Base_Test_SuperUser, Base_Test_FullCoordinator, Base_Test_ViewCoordinator
from common.baseTests.populateDatabase import createEvents

from django.test import TestCase
from django.urls import reverse

from events.models import Event, Division, Year, AvailableDivision, Venue

# Division

class Division_Base:
    modelURLName = 'events_division'
    state1Obj = 'division1_state1'
    state2Obj = 'division2_state2'
    validPayload = {
            'name': 'New Division',
            'state': 0,
        }

    def additionalSetup(self):
        createEvents(self)

    def updatePayload(self):
        self.validPayload['state'] = self.state1.id

class Test_Division_NotStaff(Division_Base, Base_Test_NotStaff, TestCase):
    pass

class Test_Division_SuperUser(Division_Base, Base_Test_SuperUser, TestCase):
    expectedListItems = 4
    expectedStrings = [
        'Division 1',
        'Division 2',
        'Division 3',
        'Division 4',
    ]
    expectedMissingStrings = []

    def testPostAddBlankState(self):
        payload = self.validPayload.copy()
        del payload['state']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 302)

class Division_Coordinators_Base(Division_Base):
    expectedListItems = 3
    expectedStrings = [
        'Division 1',
        'Division 3',
        'Division 4',
    ]
    expectedMissingStrings = [
        'Division 2',
    ]

class Test_Division_FullCoordinator(Division_Coordinators_Base, Base_Test_FullCoordinator, TestCase):
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

class Test_Division_ViewCoordinator(Division_Coordinators_Base, Base_Test_ViewCoordinator, TestCase):
    pass

# Venue

class Venue_Base:
    modelURLName = 'events_venue'
    state1Obj = 'venue1_state1'
    state2Obj = 'venue3_state2'
    validPayload = {
            'name': 'New Venue',
            'state': 0,
        }

    def additionalSetup(self):
        createEvents(self)

    def updatePayload(self):
        self.validPayload['state'] = self.state1.id

class Test_Venue_NotStaff(Venue_Base, Base_Test_NotStaff, TestCase):
    pass

class Test_Venue_SuperUser(Venue_Base, Base_Test_SuperUser, TestCase):
    expectedListItems = 3
    expectedStrings = [
        'Venue 1',
        'Venue 2',
        'Venue 3',
    ]
    expectedMissingStrings = []

    def testPostAddBlankState(self):
        payload = self.validPayload.copy()
        del payload['state']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the errors below.') # Multiple errors because of checkRequiredFieldsNotNone validation
        self.assertContains(response, 'This field is required.')

class Venue_Coordinators_Base(Venue_Base):
    expectedListItems = 2
    expectedStrings = [
        'Venue 1',
        'Venue 2',
    ]
    expectedMissingStrings = [
        'Venue 3',
    ]

class Test_Venue_FullCoordinator(Venue_Coordinators_Base, Base_Test_FullCoordinator, TestCase):
    def testPostAddBlankState(self):
        payload = self.validPayload.copy()
        del payload['state']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the errors below.') # Multiple errors because of checkRequiredFieldsNotNone validation
        self.assertContains(response, 'This field is required.')

    def testPostAddWrongState(self):
        payload = self.validPayload.copy()
        payload['state'] = self.state2.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the errors below.') # Multiple errors because of checkRequiredFieldsNotNone validation
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

class Test_Venue_ViewCoordinator(Venue_Coordinators_Base, Base_Test_ViewCoordinator, TestCase):
    pass
