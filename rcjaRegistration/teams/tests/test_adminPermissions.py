from common.baseTests.adminPermissions import Base_Test_NotStaff, Base_Test_SuperUser, Base_Test_FullCoordinator, Base_Test_ViewCoordinator
from common.baseTests.populateDatabase import createEvents, createTeams

from django.test import TestCase
from django.urls import reverse

import datetime

from teams.models import Team
from schools.models import SchoolAdministrator

# Team

class Team_Base:
    modelURLName = 'teams_team'
    state1Obj = 'state1_event1_team1'
    state2Obj = 'state2_event1_team3'
    validPayload = {
        'event': 0,
        'division': 0,
        'mentorUser': 0,
        'school': 0,
        'name': 'New Team',
        'hardwarePlatform': 0,
        'softwarePlatform': 0,
        'student_set-TOTAL_FORMS': 0,
        'student_set-INITIAL_FORMS': 0,
        'student_set-MIN_NUM_FORMS': 0,
        'student_set-MAX_NUM_FORMS': 1000,
    }

    def additionalSetup(self):
        createEvents(self)
        createTeams(self)

    def updatePayload(self):
        self.validPayload['event'] = self.state1_openCompetition.id
        self.validPayload['division'] = self.division3.id
        self.validPayload['mentorUser'] = self.user_state1_school1_mentor1.id
        self.validPayload['school'] = self.school1_state1.id
        self.validPayload['hardwarePlatform'] = self.hardwarePlatform.id
        self.validPayload['softwarePlatform'] = self.softwarePlatform.id

class Test_Team_NotStaff(Team_Base, Base_Test_NotStaff, TestCase):
    pass

class AdditionalTeamPostTestsMixin:

    def testPostAddBlankEvent(self):
        payload = self.validPayload.copy()
        del payload['event']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the errors below.')
        self.assertContains(response, 'This field is required.')

    # Campus field

    def testAddCampusField(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_add'))

        self.assertNotContains(response, 'Campus:')
        self.assertContains(response, 'You can select campus after you have clicked save.')

    def testChangeCampusField(self):
        response = self.client.get(reverse(f'admin:{self.modelURLName}_change', args=(self.state1_event1_team1.id,)))

        self.assertContains(response, 'Campus:')
        self.assertNotContains(response, 'You can select campus after you have clicked save.')

    # Test admin validation

    def testMultipleSchoolsSchoolBlank(self):
        SchoolAdministrator.objects.create(user=self.user_state1_school1_mentor1, school=self.school2_state1)

        payload = self.validPayload.copy()
        del payload['school']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, f"School must not be blank because {self.user_state1_school1_mentor1.fullname_or_email()} is an administrator of multiple schools. Please select a school.")

    def testMultipleSchoolsSchoolNotBlank(self):
        SchoolAdministrator.objects.create(user=self.user_state1_school1_mentor1, school=self.school2_state1)

        payload = self.validPayload.copy()
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)

        self.assertEqual(response.status_code, 302)

    def testNotAdminOfSchool(self):
        payload = self.validPayload.copy()
        payload['mentorUser'] = self.user_state1_school2_mentor3.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, f"is not an administrator of")

    def testRemoveSchoolDenied(self):
        payload = self.validPayload.copy()
        del payload['school']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_change', args=(self.state1_event1_team1.id,)), data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, f"remove {self.school1_state1} from this team while {self.user_state1_school1_mentor1.fullname_or_email()} is still an admin of this school.")

    # Test auto school set
    def testSchoolAutoSet(self):
        payload = self.validPayload.copy()
        del payload['school']
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload, follow=True)

        self.assertContains(response, 'was added successfully. You may edit it again below.')
        self.assertContains(response, f'({self.school1_state1}) automatically added to New Team')

class Test_Team_SuperUser(AdditionalTeamPostTestsMixin, Team_Base, Base_Test_SuperUser, TestCase):
    expectedListItems = 3
    expectedStrings = [
        'Team 1',
        'Team 2',
        'Team 3',
    ]
    expectedMissingStrings = []

class Team_Coordinators_Base(Team_Base):
    expectedListItems = 2
    expectedStrings = [
        'Team 1',
        'Team 2',
    ]
    expectedMissingStrings = [
        'Team 3',
    ]

class Test_Team_FullCoordinator(AdditionalTeamPostTestsMixin, Team_Coordinators_Base, Base_Test_FullCoordinator, TestCase):

    # Additional tests

    def testPostAddWrongEvent(self):
        payload = self.validPayload.copy()
        payload['event'] = self.state2_openCompetition.id
        response = self.client.post(reverse(f'admin:{self.modelURLName}_add'), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the errors below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

class Test_Team_ViewCoordinator(Team_Coordinators_Base, Base_Test_ViewCoordinator, TestCase):
    pass
