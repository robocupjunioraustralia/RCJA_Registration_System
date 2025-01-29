from common.baseTests import Base_Test_NotStaff, Base_Test_SuperUser, Base_Test_FullCoordinator, Base_Test_ViewCoordinator, createEvents, createWorkshopAttendees, createInvoices, POST_VALIDATION_FAILURE, POST_SUCCESS

from django.test import TestCase
from django.urls import reverse

import datetime

from schools.models import SchoolAdministrator

# WorkshopAttendee

class WorkshopAttendee_Base:
    modelName = 'Workshop attendee'
    modelURLName = 'workshops_workshopattendee'
    state1Obj = 'state1_event1_workshopAttendee1'
    state2Obj = 'state2_event1_workshopAttendee3'
    validPayload = {
        'event': 0,
        'division': 0,
        'mentorUser': 0,
        'school': 0,
        'firstName': 'New First',
        'lastName': 'New Last',
        'yearLevel': '5',
        'attendeeType': 'student',
        'gender': 'male',
    }

    @classmethod
    def additionalSetup(cls):
        createEvents(cls)
        createInvoices(cls)
        createWorkshopAttendees(cls)

    @classmethod
    def updatePayload(cls):
        cls.validPayload['event'] = cls.state1_openWorkshop.id
        cls.validPayload['division'] = cls.division3.id
        cls.validPayload['mentorUser'] = cls.user_state1_school1_mentor1.id
        cls.validPayload['school'] = cls.school1_state1.id

class Test_WorkshopAttendee_NotStaff(WorkshopAttendee_Base, Base_Test_NotStaff, TestCase):
    pass

class AdditionalWorkshopAttendeePostTestsMixin:

    def testPostAddBlankEvent(self):
        payload = self.validPayload.copy()
        del payload['event']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, POST_VALIDATION_FAILURE)
        self.assertContains(response, 'Please correct the errors below.')
        self.assertContains(response, 'This field is required.')

    # Campus field

    def testAddCampusField(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_add'))

        self.assertNotContains(response, 'Campus:')
        self.assertContains(response, 'You can select campus after you have clicked save.')

    def testChangeCampusField(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1_event1_workshopAttendee1.id,)))

        self.assertContains(response, 'Campus:')
        self.assertNotContains(response, 'You can select campus after you have clicked save.')

    # Test admin validation

    def testPostCompetitionEvent(self):
        payload = self.validPayload.copy()
        payload['event'] = self.state1_openCompetition.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, POST_VALIDATION_FAILURE)
        self.assertContains(response, 'Please correct the errors below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

    def testMultipleSchoolsSchoolBlank(self):
        SchoolAdministrator.objects.create(user=self.user_state1_school1_mentor1, school=self.school2_state1)

        payload = self.validPayload.copy()
        del payload['school']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)

        self.assertEqual(response.status_code, POST_VALIDATION_FAILURE)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, f"School must not be blank because {self.user_state1_school1_mentor1.fullname_or_email()} is an administrator of multiple schools. Please select a school.")

    def testMultipleSchoolsSchoolNotBlank(self):
        SchoolAdministrator.objects.create(user=self.user_state1_school1_mentor1, school=self.school2_state1)

        payload = self.validPayload.copy()
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)

        self.assertEqual(response.status_code, POST_SUCCESS)

    def testNotAdminOfSchool(self):
        payload = self.validPayload.copy()
        payload['mentorUser'] = self.user_state1_school2_mentor3.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)

        self.assertEqual(response.status_code, POST_VALIDATION_FAILURE)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, f"is not an administrator of")

    def testRemoveSchoolDenied(self):
        payload = self.validPayload.copy()
        del payload['school']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_change', args=(self.state1_event1_workshopAttendee1.id,)), data=payload)

        self.assertEqual(response.status_code, POST_VALIDATION_FAILURE)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, f"remove {self.school1_state1} from this team while {self.user_state1_school1_mentor1.fullname_or_email()} is still an admin of this school.")

    # Test auto school set
    def testSchoolAutoSet(self):
        payload = self.validPayload.copy()
        del payload['school']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload, follow=True)

        self.assertContains(response, 'was added successfully. You may edit it again below.')
        self.assertContains(response, f'({self.school1_state1}) automatically added to New First New Last')

    # Test invoice override
    def testPostInvoiceOverride_success(self):
        payload = self.validPayload.copy()
        payload['invoiceOverride'] = self.state1_workshopEvent1_invoice1.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)), data=payload)

        self.assertEqual(response.status_code, POST_SUCCESS)

    def testPostInvoiceOverride_wrong_event(self):
        payload = self.validPayload.copy()
        payload['invoiceOverride'] = self.state2_workshopEvent1_invoice2.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)), data=payload)

        self.assertEqual(response.status_code, POST_VALIDATION_FAILURE)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

    # Test autocomplete filtering
    def test_event_autocomplete_contains_no_competitions(self):
        response = self.client.get(reverse('admin:autocomplete')+f"?app_label=workshops&model_name=workshopattendee&field_name=event", HTTP_REFERER=reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))

        self.assertNotContains(response, self.state1_openCompetition.name)

class Test_WorkshopAttendee_SuperUser(AdditionalWorkshopAttendeePostTestsMixin, WorkshopAttendee_Base, Base_Test_SuperUser, TestCase):
    expectedListItems = 3
    expectedStrings = [
        'First 1 Last 1',
        'First 2 Last 2',
        'First 3 Last 3',
    ]
    expectedMissingStrings = []

    def test_event_autocomplete_contains_correct_workshops(self):
        response = self.client.get(reverse('admin:autocomplete')+f"?app_label=workshops&model_name=workshopattendee&field_name=event", HTTP_REFERER=reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))

        self.assertContains(response, self.state1_openWorkshop.name)
        self.assertContains(response, self.state2_openWorkshop.name)

class WorkshopAttendee_Coordinators_Base(WorkshopAttendee_Base):
    expectedListItems = 2
    expectedStrings = [
        'First 1 Last 1',
        'First 2 Last 2',
    ]
    expectedMissingStrings = [
        'First 3 Last 3',
    ]

class Test_WorkshopAttendee_FullCoordinator(AdditionalWorkshopAttendeePostTestsMixin, WorkshopAttendee_Coordinators_Base, Base_Test_FullCoordinator, TestCase):

    # Additional tests

    def testPostAddWrongEvent(self):
        payload = self.validPayload.copy()
        payload['event'] = self.state2_openWorkshop.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, POST_VALIDATION_FAILURE)
        self.assertContains(response, 'Please correct the errors below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

    def test_event_autocomplete_contains_correct_workshops(self):
        from coordination.models import Coordinator
        self.coord_state2_viewcoordinator = Coordinator.objects.create(user=self.user_state1_fullcoordinator, state=self.state2, permissionLevel='viewall', position='Text')
        response = self.client.get(reverse('admin:autocomplete')+f"?app_label=workshops&model_name=workshopattendee&field_name=event", HTTP_REFERER=reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))

        self.assertContains(response, self.state1_openWorkshop.name)
        self.assertNotContains(response, self.state2_openWorkshop.name)

class Test_WorkshopAttendee_ViewCoordinator(WorkshopAttendee_Coordinators_Base, Base_Test_ViewCoordinator, TestCase):
    def test_event_autocomplete_contains_correct_workshops(self):
        response = self.client.get(reverse('admin:autocomplete')+f"?app_label=workshops&model_name=workshopattendee&field_name=event", HTTP_REFERER=reverse(f'admin:{self.modelURLName}_change', args=(self.state1ObjID,)))

        self.assertNotContains(response, self.state1_openWorkshop.name)
        self.assertNotContains(response, self.state2_openWorkshop.name)
