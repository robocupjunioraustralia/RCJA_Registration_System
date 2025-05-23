from common.baseTests import createStates, createUsers, createSchools, createEvents, createTeams, createWorkshopAttendees

from django.test import TestCase
from django.urls import reverse
from django.http import HttpRequest

import datetime

from schools.models import School, Campus
from teams.models import Team
from workshops.models import WorkshopAttendee
from invoices.models import Invoice

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
            self.assertTrue(hasattr(eventAttendee, 'oldSchool'))
            self.assertTrue(hasattr(eventAttendee, 'school'))

    def test_validate_loads_different_schools_keep_campuses(self):
        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': True,
            'school1NewCampusName': '',
            'school2NewCampusName': '',
        })
        self.assertEqual(response.status_code, 200)

    def test_validate_context_different_schools_keep_campuses(self):
        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': True,
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
            self.assertTrue(hasattr(campus, 'school'))
            self.assertTrue(hasattr(campus, 'oldSchool'))
        
    def test_validate_loads_different_schools_new_campuses(self):
        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': False,
            'school1NewCampusName': 'New Campus 1',
            'school2NewCampusName': 'New Campus 2',
        })
        self.assertEqual(response.status_code, 200)
    
    def test_validate_context_different_schools_new_campuses(self):
        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': False,
            'school1NewCampusName': 'New Campus 1',
            'school2NewCampusName': 'New Campus 2',
        })
        self.assertIn(self.campus1_school1, response.context['campusChanges'])
        self.assertIn(self.campus2_school1, response.context['campusChanges'])
        self.assertIn(self.campus3_school2, response.context['campusChanges'])
        self.assertIn(self.campus4_school2, response.context['campusChanges'])
        self.assertNotIn(self.campus5_school3, response.context['campusChanges'])

        self.assertEqual(len(response.context['campusChanges']), 6)

        for campus in response.context['campusChanges']:
            self.assertTrue(hasattr(campus, 'oldSchool'))

        for eventAttendee in response.context['eventAttendeeChanges']:
            self.assertEqual(eventAttendee.school, self.school1_state1)
            self.assertTrue(hasattr(eventAttendee, 'oldSchool'))

    def test_validate_loads_different_schools_campus_reused(self):
        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': False,
            'school1NewCampusName': 'Campus 1',
            'school2NewCampusName': 'Campus 3',
        })
        self.assertEqual(response.status_code, 200)
    
    def test_validate_context_different_schools_campus_reused(self):
        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': False,
            'school1NewCampusName': 'Campus 1',
            'school2NewCampusName': 'Campus 3',
        })
        self.assertIn(self.campus1_school1, response.context['campusChanges'])
        self.assertIn(self.campus2_school1, response.context['campusChanges'])
        self.assertIn(self.campus3_school2, response.context['campusChanges'])
        self.assertIn(self.campus4_school2, response.context['campusChanges'])
        self.assertNotIn(self.campus5_school3, response.context['campusChanges'])

        self.assertEqual(len(response.context['campusChanges']), 4)

    def test_validate_loads_same_school(self):
        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school1_state1.id]), {})
        self.assertEqual(response.status_code, 200)

    def test_validate_context_same_school(self):
        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school1_state1.id]), {})
        self.assertIn(self.campus1_school1, response.context['campusChanges'])
        self.assertIn(self.campus2_school1, response.context['campusChanges'])
        self.assertNotIn(self.campus3_school2, response.context['campusChanges'])
        self.assertNotIn(self.campus4_school2, response.context['campusChanges'])
        self.assertNotIn(self.campus5_school3, response.context['campusChanges'])

        self.assertEqual(len(response.context['campusChanges']), 2)
    
    def test_merge_different_schools_no_new_campuses(self):
        self.assertTrue(School.objects.filter(id=self.school2_state1.id).exists())
        self.assertTrue(Campus.objects.filter(school=self.school1_state1).exists())
        self.assertEqual(Team.objects.filter(school=self.school1_state1).count(), 3)

        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': False,
            'school1NewCampusName': '',
            'school2NewCampusName': '',
            'merge': "",
        })

        self.assertEqual(response.status_code, 302)

        self.assertTrue(School.objects.filter(id=self.school1_state1.id).exists())
        self.assertFalse(School.objects.filter(id=self.school2_state1.id).exists())
        self.assertEqual(Campus.objects.filter(school=self.school1_state1).count(), 0)

        self.assertEqual(Team.objects.filter(school=self.school1_state1).count(), 5)
        self.assertEqual(WorkshopAttendee.objects.filter(school=self.school1_state1).count(), 3)

    def test_merge_different_schools_keep_campuses(self):
        self.assertTrue(School.objects.filter(id=self.school2_state1.id).exists())
        self.assertTrue(Campus.objects.filter(school=self.school1_state1).exists())
        self.assertEqual(Team.objects.filter(school=self.school1_state1).count(), 3)

        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': True,
            'school1NewCampusName': '',
            'school2NewCampusName': '',
            'merge': "",
        })

        self.assertEqual(response.status_code, 302)

        self.assertTrue(School.objects.filter(id=self.school1_state1.id).exists())
        self.assertFalse(School.objects.filter(id=self.school2_state1.id).exists())
        self.assertEqual(Campus.objects.filter(school=self.school1_state1).count(), 4)

        self.assertEqual(Team.objects.filter(school=self.school1_state1).count(), 5)
        self.assertEqual(WorkshopAttendee.objects.filter(school=self.school1_state1).count(), 3)

    def test_merge_different_schools_new_campuses(self):
        self.assertTrue(School.objects.filter(id=self.school2_state1.id).exists())
        self.assertTrue(Campus.objects.filter(school=self.school1_state1).exists())
        self.assertEqual(Team.objects.filter(school=self.school1_state1).count(), 3)

        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': False,
            'school1NewCampusName': 'New Campus 1',
            'school2NewCampusName': 'New Campus 2',
            'merge': "",
        })

        self.assertEqual(response.status_code, 302)

        self.assertTrue(School.objects.filter(id=self.school1_state1.id).exists())
        self.assertFalse(School.objects.filter(id=self.school2_state1.id).exists())
        self.assertEqual(Campus.objects.filter(school=self.school1_state1).count(), 2)

        self.assertEqual(Team.objects.filter(school=self.school1_state1).count(), 5)
        self.assertEqual(WorkshopAttendee.objects.filter(school=self.school1_state1).count(), 3)

    def test_merge_different_schools_campus_reused(self):
        self.assertTrue(School.objects.filter(id=self.school2_state1.id).exists())
        self.assertTrue(Campus.objects.filter(school=self.school1_state1).exists())
        self.assertEqual(Team.objects.filter(school=self.school1_state1).count(), 3)

        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': False,
            'school1NewCampusName': 'Campus 1',
            'school2NewCampusName': 'Campus 3',
            'merge': "",
        })

        self.assertEqual(response.status_code, 302)

        self.assertTrue(School.objects.filter(id=self.school1_state1.id).exists())
        self.assertFalse(School.objects.filter(id=self.school2_state1.id).exists())
        self.assertEqual(Campus.objects.filter(school=self.school1_state1).count(), 2)

        self.assertEqual(Team.objects.filter(school=self.school1_state1).count(), 5)
        self.assertEqual(WorkshopAttendee.objects.filter(school=self.school1_state1).count(), 3)

    def test_merge_same_school(self):
        self.assertTrue(School.objects.filter(id=self.school1_state1.id).exists())
        self.assertTrue(Campus.objects.filter(school=self.school1_state1).exists())
        self.assertEqual(Team.objects.filter(school=self.school1_state1).count(), 3)

        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school1_state1.id]), {
            'merge': "",
        })

        self.assertEqual(response.status_code, 302)

        self.assertTrue(School.objects.filter(id=self.school1_state1.id).exists())
        self.assertEqual(Campus.objects.filter(school=self.school1_state1).count(), 0)

        self.assertEqual(Team.objects.filter(school=self.school1_state1).count(), 3)
        self.assertEqual(WorkshopAttendee.objects.filter(school=self.school1_state1).count(), 3)

    def test_non_zero_invoices_not_deleted(self):
        self.assertEqual(Invoice.objects.filter(school=self.school1_state1).count(), 4)
        self.assertEqual(Invoice.objects.filter(school=self.school2_state1).count(), 1)

        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': False,
            'school1NewCampusName': '',
            'school2NewCampusName': '',
            'merge': "",
        })

        self.assertEqual(Invoice.objects.filter(school=self.school1_state1).count(), 5)
        self.assertEqual(Invoice.objects.filter(school=self.school2_state1).count(), 0)

    def test_zero_invoices_deleted(self):
        Invoice.objects.create(school=self.school1_state1, event=self.state1_closedCompetition1, invoiceToUser=self.user_state1_school1_mentor1, campus=self.campus1_school1)
        Invoice.objects.create(school=self.school2_state1, event=self.state1_closedCompetition1, invoiceToUser=self.user_state1_school2_mentor3, campus=self.campus3_school2)

        self.assertEqual(Invoice.objects.filter(school=self.school1_state1).count(), 5)
        self.assertEqual(Invoice.objects.filter(school=self.school2_state1).count(), 2)

        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': False,
            'school1NewCampusName': '',
            'school2NewCampusName': '',
            'merge': "",
        })

        self.assertEqual(Invoice.objects.filter(school=self.school1_state1).count(), 5)
        self.assertEqual(Invoice.objects.filter(school=self.school2_state1).count(), 0)

    def test_invoice_clash_school1_exception_raised(self):
        self.newInvoice1 = Invoice.objects.create(school=self.school1_state1, event=self.state1_closedCompetition1, invoiceToUser=self.user_state1_school1_mentor1)
        self.newInvoice2 = Invoice.objects.create(school=self.school1_state1, event=self.state1_closedCompetition1, invoiceToUser=self.user_state1_school1_mentor1, campus=self.campus1_school1)

        self.newInvoice1.invoicepayment_set.create(amountPaid=100, datePaid=datetime.datetime.today())
        self.newInvoice2.invoicepayment_set.create(amountPaid=100, datePaid=datetime.datetime.today())

        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': False,
            'school1NewCampusName': '',
            'school2NewCampusName': '',
            'merge': "",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "because already a conflicting invoice")

    def test_invoice_clash_school2_exception_raised(self):
        self.newInvoice = Invoice.objects.create(school=self.school2_state1, event=self.state1_closedCompetition1, invoiceToUser=self.user_state1_school1_mentor1, campus=self.campus3_school2)

        self.newInvoice.invoicepayment_set.create(amountPaid=100, datePaid=datetime.datetime.today())

        response = self.client.post(reverse('schools:adminMergeSchools', args=[self.school1_state1.id, self.school2_state1.id]), {
            'keepExistingCampuses': False,
            'school1NewCampusName': '',
            'school2NewCampusName': '',
            'merge': "",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "because already a conflicting invoice")
