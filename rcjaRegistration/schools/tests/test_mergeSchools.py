from common.baseTests import createStates, createUsers, createSchools, createEvents, createTeams, createWorkshopAttendees

from django.test import TestCase
from django.urls import reverse
from django.http import HttpRequest

from schools.models import School, Campus
from teams.models import Team
from workshops.models import WorkshopAttendee

def createAdditionalTeamsAndWorkshopAttendees(obj):
    obj.school2_team1 = Team.objects.create(school=obj.school2_state1, event=obj.state1_closedCompetition1, division=obj.division1_state1, mentorUser=obj.user_state1_school2_mentor3, name='School 2 Team 1')
    obj.school2_team2 = Team.objects.create(school=obj.school2_state1, event=obj.state1_closedCompetition1, division=obj.division1_state1, mentorUser=obj.user_state1_school2_mentor3, name='School 2 Team 2')
    obj.school3_workshopAttendee1 = WorkshopAttendee.objects.create(school=obj.school3_state2, event=obj.state1_openWorkshop, division=obj.division3, mentorUser=obj.user_state2_school3_mentor4, firstName='Frank', lastName='Smith', attendeeType='student', yearLevel='5', gender='other')

class Base_Test_MergeSchools(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createSchools(cls)
        createEvents(cls)
        createTeams(cls)
        createWorkshopAttendees(cls)
        createAdditionalTeamsAndWorkshopAttendees(cls)
    
class Test_MergeSchools_notstaff(Base_Test_MergeSchools, TestCase):
    def setUp(self):
        self.client.login(request=HttpRequest(), username=self.email_user_notstaff, password=self.password)

    def test_permission_denied(self):
        response = self.client.get(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]))
        self.assertEqual(response.status_code, 403)

class Test_MergeSchools_staff_otherstate(Base_Test_MergeSchools, TestCase):
    def setUp(self):
        self.client.login(request=HttpRequest(), username=self.email_user_state2_fullcoordinator, password=self.password)

    def test_permission_denied(self):
        response = self.client.get(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]))
        self.assertEqual(response.status_code, 403)

class Test_MergeSchools_superuser(Base_Test_MergeSchools, TestCase):    
    def setUp(self):
        self.client.login(request=HttpRequest(), username=self.email_user_state1_super1, password=self.password)

    def test_page_loads(self):
        response = self.client.get(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]))
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        response = self.client.get(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]))
        self.assertTemplateUsed(response, 'schools/adminMergeSchools.html')

    def test_school_does_not_exist(self):
        self.assertFalse(School.objects.filter(id=9999).exists())
        response = self.client.get(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, 9999]))
        self.assertEqual(response.status_code, 404)

    def test_page_content_different_schools(self):
        response = self.client.get(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]))
        self.assertContains(response, f'Merging {self.school2_state1} into {self.school1_state1}')
        self.assertContains(response, 'Campus names')
        self.assertContains(response, 'Swap merge order')

    def test_page_content_same_schools(self):
        response = self.client.get(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school1_state1.id]))
        self.assertContains(response, f'Merging campuses for {self.school1_state1}')
        self.assertNotContains(response, 'Campus names')
        self.assertNotContains(response, 'Swap merge order')

    def test_validate_loads_different_schools_no_new_campuses(self):
        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': False,
            'school1NewCampusName': '',
            'school2NewCampusName': '',
        })
        self.assertEqual(response.status_code, 200)

    def test_validate_context_different_schools_no_new_campuses(self):
        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': False,
            'school1NewCampusName': '',
            'school2NewCampusName': '',
        })
        self.assertIn(self.campus1_school1, response.context['campusChanges'])
        self.assertIn(self.campus2_school1, response.context['campusChanges'])
        self.assertIn(self.campus3_school2, response.context['campusChanges'])
        self.assertIn(self.campus4_school2, response.context['campusChanges'])
        self.assertNotIn(self.campus5_school3, response.context['campusChanges'])

        self.assertEqual(len(response.context['campusChanges']), 4)

        for campus in response.context['campusChanges']:
            self.assertTrue(hasattr(campus, 'oldSchool'))
        
        self.assertIn(self.state1_event1_team1, response.context['eventAttendeeChanges'])
        self.assertIn(self.state1_event1_team2, response.context['eventAttendeeChanges'])
        self.assertIn(self.state2_event1_team3, response.context['eventAttendeeChanges'])
        self.assertIn(self.state1_event1_workshopAttendee1, response.context['eventAttendeeChanges'])
        self.assertIn(self.state1_event1_workshopAttendee2, response.context['eventAttendeeChanges'])
        self.assertIn(self.state2_event1_workshopAttendee3, response.context['eventAttendeeChanges'])
        self.assertIn(self.school2_team1, response.context['eventAttendeeChanges'])
        self.assertIn(self.school2_team2, response.context['eventAttendeeChanges'])
        self.assertNotIn(self.school3_workshopAttendee1, response.context['eventAttendeeChanges'])
        for eventAttendee in response.context['eventAttendeeChanges']:
            self.assertEqual(eventAttendee.school, self.school1_state1)
