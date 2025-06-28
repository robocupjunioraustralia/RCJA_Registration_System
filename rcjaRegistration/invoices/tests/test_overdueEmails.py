from django.test import TestCase
from django.urls import reverse
from django.http import HttpRequest
from django.core import mail

from invoices.models import InvoiceGlobalSettings, Invoice
from invoices.forms import EVENTS_CHOICES
from users.models import User
from regions.models import State, Region
from schools.models import School, SchoolAdministrator
from teams.models import Team, Student
from events.models import Event, Year, Division

import datetime

def commonSetUp(self):
    self.user1 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email1, password=self.password)
    self.user2 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email2, password=self.password)
    self.user3 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email3, password=self.password)
    self.superUser = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_superUser, password=self.password, is_superuser=True)

    self.state1 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='Victoria', abbreviation='VIC')
    self.state2 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='NSW', abbreviation='NSW')
    self.region1 = Region.objects.create(name='Test Region', description='test desc')

    self.school1 = School.objects.create(name='School 1', state=self.state1, region=self.region1)
    self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user1)
    self.school2 = School.objects.create(name='School 2', state=self.state1, region=self.region1)
    self.schoolAdmin2 = SchoolAdministrator.objects.create(school=self.school2, user=self.user2)
    self.school3 = School.objects.create(name='School 3', state=self.state1, region=self.region1)
    self.schoolAdmin3 = SchoolAdministrator.objects.create(school=self.school3, user=self.user3)

    self.year = Year.objects.create(year=2020)

    self.eventDueToday = Event.objects.create(
        year=self.year,
        state=self.state1,
        name='Due Today',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        entryFeeIncludesGST=True,
        competition_billingType='team',
        competition_defaultEntryFee = 50,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        registrationsCloseDate = (datetime.datetime.now()).date(),
        paymentDueDate = (datetime.datetime.now()).date(),
        directEnquiriesTo = self.user1,
    )
    self.eventDueYesterday = Event.objects.create(
        year=self.year,
        state=self.state1,
        name='Due Yesterday',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        entryFeeIncludesGST=True,
        competition_billingType='team',
        competition_defaultEntryFee = 50,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
        paymentDueDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
        directEnquiriesTo = self.user1,
    )

    self.eventDue21Days = Event.objects.create(
        year=self.year,
        state=self.state1,
        name='Due 21 Days',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        entryFeeIncludesGST=True,
        competition_billingType='team',
        competition_defaultEntryFee = 50,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-21)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-21)).date(),
        paymentDueDate = (datetime.datetime.now() + datetime.timedelta(days=-21)).date(),
        directEnquiriesTo = self.user1,
    )

    self.eventDue22Days = Event.objects.create(
        year=self.year,
        state=self.state1,
        name='Due 22 Days',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        entryFeeIncludesGST=True,
        competition_billingType='team',
        competition_defaultEntryFee = 50,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-22)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-22)).date(),
        paymentDueDate = (datetime.datetime.now() + datetime.timedelta(days=-22)).date(),
        directEnquiriesTo = self.user1,
    )

    self.eventDue42Days = Event.objects.create(
        year=self.year,
        state=self.state1,
        name='Due 42 Days',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        entryFeeIncludesGST=True,
        competition_billingType='team',
        competition_defaultEntryFee = 50,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-42)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-42)).date(),
        paymentDueDate = (datetime.datetime.now() + datetime.timedelta(days=-42)).date(),
        directEnquiriesTo = self.user1,
    )

    self.eventDue43Days = Event.objects.create(
        year=self.year,
        state=self.state1,
        name='Due 43 Days',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        entryFeeIncludesGST=True,
        competition_billingType='team',
        competition_defaultEntryFee = 50,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-43)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-43)).date(),
        paymentDueDate = (datetime.datetime.now() + datetime.timedelta(days=-43)).date(),
        directEnquiriesTo = self.user1,
    )

    self.division1 = Division.objects.create(name='Division 1')
    self.division2 = Division.objects.create(name='Division 2')
    self.division3 = Division.objects.create(name='Division 3')

    self.invoiceSettings = InvoiceGlobalSettings.objects.create(
        invoiceFromName='From Name',
        invoiceFromDetails='Test Details Text',
        invoiceFooterMessage='Test Footer Text',
    )

def createTeams(self, event, school, campuses=None,):
    self.teams = []
    for division in [self.division1, self.division2, self.division3]:
        if campuses is not None:
            for j in range(2):
                for campus in self.campuses:
                    self.teams.append(
                        Team.objects.create(
                            event=self.event,
                            school=school,
                            campus=campus,
                            mentorUser=self.user1,
                            name=f'Team {j}{division}{campus}',
                            division=division,
                        )
                    )
        else:
            for j in range(4):
                self.teams.append(
                    Team.objects.create(
                        event=event,
                        school=school,
                        mentorUser=self.user1,
                        name=f'Team {j}{division}',
                        division=division,
                    )
                )

def createStudents(self):
    self.students = []
    for team in self.teams:
        for i in range(3):
            self.students.append(
                Student.objects.create(
                    team=team,
                    firstName='First name',
                    lastName='Last name',
                    yearLevel=5,
                    gender='other',
                )
            )

class TestOverdueEmails(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        commonSetUp(self)
        for event in Event.objects.all():
            createTeams(self, event, self.school1)
        createStudents(self)
        self.invoice0 = Invoice.objects.get(event=self.eventDueToday, school=self.school1)
        self.invoice1 = Invoice.objects.get(event=self.eventDueYesterday, school=self.school1)
        self.invoice21 = Invoice.objects.get(event=self.eventDue21Days, school=self.school1)
        self.invoice22 = Invoice.objects.get(event=self.eventDue22Days, school=self.school1)
        self.invoice42 = Invoice.objects.get(event=self.eventDue42Days, school=self.school1)
        self.invoice43 = Invoice.objects.get(event=self.eventDue43Days, school=self.school1)

    def testLoginRequired(self):
        url = reverse('invoices:overdueEmails')
    
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/invoices/overdueEmails/")
        self.assertEqual(response.status_code, 302)

    def testMemberAccess(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        url = reverse('invoices:overdueEmails')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to view this page", status_code=403)

    def testStaffAccess(self):
        self.client.login(request=HttpRequest(), username=self.email_superUser, password=self.password)
        url = reverse('invoices:overdueEmails')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def testAvailableEvents(self):
        self.client.login(request=HttpRequest(), username=self.email_superUser, password=self.password)
        url = reverse('invoices:overdueEmails')
        response = self.client.get(url)
        names = ['Due Yesterday','Due 21 Days','Due 22 Days','Due 42 Days',"Due 43 Days",]
        for name in names:
            self.assertContains(response, name)
        self.assertNotContains(response, 'Due Today')

    def testEventsGiven(self):
        request=HttpRequest()
        request.user = self.superUser
        returned_events = list(EVENTS_CHOICES(request))
        events = [self.eventDueYesterday, self.eventDue21Days, self.eventDue22Days,self.eventDue42Days,self.eventDue43Days]
        for event in events:
            self.assertIn((event.pk, event.name), returned_events)
        self.assertNotIn((self.eventDueToday.pk, self.eventDueToday.name),returned_events)

    def testEmailsSent(self):
        self.client.login(request=HttpRequest(), username=self.email_superUser, password=self.password)
        url = reverse('invoices:overdueEmails')

        events = [self.eventDueYesterday, self.eventDue21Days, self.eventDue22Days,self.eventDue42Days,self.eventDue43Days]
        for event in events:
            data = {'events':event.pk}
            self.client.post(url, data=data)
            
        self.assertIn("is overdue",mail.outbox[0].body)
        self.assertIn("is overdue",mail.outbox[1].body)
        self.assertIn("is well overdue",mail.outbox[2].body)
        self.assertIn("is well overdue",mail.outbox[3].body)
        self.assertIn("is beyond overdue",mail.outbox[4].body)

        self.assertEqual(5,len(mail.outbox))
        