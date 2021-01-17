from common.baseTests.adminPermissions import Base_Test_NotStaff, Base_Test_SuperUser, Base_Test_FullCoordinator, Base_Test_ViewCoordinator
from common.baseTests.populateDatabase import createEvents

from django.test import TestCase
from django.urls import reverse

import datetime

from events.models import Event, Division, Year, AvailableDivision, Venue
from teams.models import Team

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

# Event

class Event_Base:
    modelURLName = 'events_event'
    state1Obj = 'state1_openCompetition'
    state2Obj = 'state2_openCompetition'
    validPayload = {
        'year': 0,
        'state': 0,
        'name': 'New Event',
        'eventType': 'competition',
        'event_defaultEntryFee': 50,
        'status': 'published', # Needed for change tests
        'event_billingType': 'team', # Needed for change tests
        'maxMembersPerTeam': 5, # Needed for change tests
        'startDate': (datetime.datetime.now() + datetime.timedelta(days=15)).date(),
        'endDate': (datetime.datetime.now() + datetime.timedelta(days=15)).date(),
        'registrationsOpenDate': (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        'registrationsCloseDate': (datetime.datetime.now() + datetime.timedelta(days=1)).date(),
        'directEnquiriesTo': 0,
        'availabledivision_set-TOTAL_FORMS': 0,
        'availabledivision_set-INITIAL_FORMS': 0,
        'availabledivision_set-MIN_NUM_FORMS': 0,
        'availabledivision_set-MAX_NUM_FORMS': 1000,
        'eventavailablefiletype_set-TOTAL_FORMS': 0,
        'eventavailablefiletype_set-INITIAL_FORMS': 0,
        'eventavailablefiletype_set-MIN_NUM_FORMS': 0,
        'eventavailablefiletype_set-MAX_NUM_FORMS': 1000,
    }

    def additionalSetup(self):
        createEvents(self)

    def updatePayload(self):
        self.validPayload['state'] = self.state1.id
        self.validPayload['directEnquiriesTo'] = self.user_state1_super1.id
        self.validPayload['year'] = self.year.year

class Test_Event_NotStaff(Event_Base, Base_Test_NotStaff, TestCase):
    pass

class AdditionalEventTestsMixin:
    def testPostAddBlankState(self):
        payload = self.validPayload.copy()
        del payload['state']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the errors below.') # Multiple errors because of checkRequiredFieldsNotNone validation
        self.assertContains(response, 'This field is required.')

    def testNoStatusFieldOnAdd(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_add'))

        self.assertNotContains(response, '<label>Status:</label>')
        self.assertNotContains(response, '<select name="status" id="id_status">')

    def testDraftCorrectReadonlyFields(self):
        self.state1_openCompetition.status = 'draft'
        self.state1_openCompetition.save()

        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1_openCompetition.id,)))
        self.checkReadonly(response, [
            ('eventType', 'Event type'),
        ])
        self.checkEditable(response, [
            ('status', 'Status'),
        ])

    def testPublishedWithTeamsCorrectReadonlyFields(self):
        Team.objects.create(event=self.state1_openCompetition, division=self.division3, mentorUser=self.user_state1_super1, name='Test Team')

        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1_openCompetition.id,)))

        self.checkReadonly(response, [
            ('eventType', 'Event type'),
            ('status', 'Status'),
        ])

class Test_Event_SuperUser(AdditionalEventTestsMixin, Event_Base, Base_Test_SuperUser, TestCase):
    expectedListItems = 6
    expectedStrings = [
        'State 1 Open Competition',
        'State 1 Open Workshop',
        'State 1 Closed Competition 1',
        'State 1 Closed Competition 2',
        'State 1 Past Competition',
        'State 2 Open Competition',
    ]
    expectedMissingStrings = []

    # Inlines

    expectedAddInlines = []
    expectedMissingAddInlines = [
        'Available Divisions',
        'Event Available File Types',
    ]
    expectedChangeInlines = [
        'Available Divisions',
        'Event Available File Types',
    ]
    expectedMissingChangeInlines = []

    # Readonly fields

    expectedAddEditableFields = [
        ('eventType', 'Event type'),
    ]
    expectedAddReadonlyFields = [
    ]
    expectedChangeEditableFields = [
        ('status', 'Status'), # No teams or invoices created in setup data
    ]
    expectedChangeReadonlyFields = [
        ('eventType', 'Event type'),
    ]

class Event_Coordinators_Base(Event_Base):
    expectedListItems = 5
    expectedStrings = [
        'State 1 Open Competition',
        'State 1 Open Workshop',
        'State 1 Closed Competition 1',
        'State 1 Closed Competition 2',
        'State 1 Past Competition',
    ]
    expectedMissingStrings = [
        'State 2 Open Competition',
    ]

class Test_Event_FullCoordinator(AdditionalEventTestsMixin, Event_Coordinators_Base, Base_Test_FullCoordinator, TestCase):

    # Inlines

    expectedAddInlines = []
    expectedMissingAddInlines = [
        'Available Divisions',
        'Event Available File Types',
    ]
    expectedChangeInlines = [
        'Available Divisions',
        'Event Available File Types',
    ]
    expectedMissingChangeInlines = []

    # Readonly fields

    expectedAddEditableFields = [
        ('eventType', 'Event type'),
    ]
    expectedAddReadonlyFields = [
    ]
    expectedChangeEditableFields = [
        ('status', 'Status'), # No teams or invoices created in setup data
    ]
    expectedChangeReadonlyFields = [
        ('eventType', 'Event type'),
    ]

    # Additional tests

    def testPostAddWrongState(self):
        payload = self.validPayload.copy()
        payload['state'] = self.state2.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the errors below.') # Multiple errors because of checkRequiredFieldsNotNone validation
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

class Test_Event_ViewCoordinator(Event_Coordinators_Base, Base_Test_ViewCoordinator, TestCase):
    pass
