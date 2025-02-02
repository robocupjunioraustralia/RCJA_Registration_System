from common.baseTests import createStates, createUsers, createSchools, createEvents, createTeams, createWorkshopAttendees

from django.test import TestCase
from django.urls import reverse
from django.http import HttpRequest

class Base_Test_MergeSchools(TestCase):
    @classmethod
    def setUpTestData(cls):
        createStates(cls)
        createUsers(cls)
        createSchools(cls)
        createEvents(cls)
        createTeams(cls)
        createWorkshopAttendees(cls)
    
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
