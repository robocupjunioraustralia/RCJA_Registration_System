from django.test import TestCase
from django.urls import reverse
from django.http import HttpRequest
from django.core.exceptions import ValidationError

from invoices.models import InvoiceGlobalSettings, Invoice, InvoicePayment
from users.models import User
from regions.models import State, Region
from schools.models import School, SchoolAdministrator, Campus
from events.models import Event, Year, Division, AvailableDivision
from coordination.models import Coordinator
from .models import Team, Student, HardwarePlatform, SoftwarePlatform

import datetime
# Create your tests here.

def commonSetUp(obj): #copied from events, todo refactor
    obj.username = 'user@user.com'
    obj.password = 'password'
    obj.user = user = User.objects.create_user(email=obj.username, password=obj.password)
    obj.newState = State.objects.create(
        typeRegistration=True,
        name='Victoria',
        abbreviation='VIC'
    )
    obj.newRegion = Region.objects.create(
        name='Test Region',
        description='test desc'
    )
    obj.newSchool = School.objects.create(
        name='Melbourne High',
        abbreviation='MHS',
        state=obj.newState,
        region=obj.newRegion
    )
    obj.schoolAdministrator = SchoolAdministrator.objects.create(
        school=obj.newSchool,
        user=obj.user
    )
    obj.year = Year.objects.create(year=2019)
    obj.division = Division.objects.create(name='test')

    obj.oldEvent = Event.objects.create(
        year=obj.year,
        state=obj.newState,
        name='test old not reg',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        event_defaultEntryFee = 4,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
        directEnquiriesTo = obj.user     
    )
    obj.oldEvent.divisions.add(obj.division)

    obj.newEvent = Event.objects.create(
        year=obj.year,
        state=obj.newState,
        name='test new not reg',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        event_defaultEntryFee = 4,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=3)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=4)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-2)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+2)).date(),
        directEnquiriesTo = obj.user     
    )
    obj.newEvent.divisions.add(obj.division)

    obj.oldEventWithTeams = Event.objects.create(
        year=obj.year,
        state=obj.newState,
        name='test old yes reg',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        event_defaultEntryFee = 4,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=-3)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=-4)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-6)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
        directEnquiriesTo = obj.user     
    )
    obj.oldEventWithTeams.divisions.add(obj.division)
    obj.oldEventTeam = Team.objects.create(event=obj.oldEventWithTeams, division=obj.division, school=obj.newSchool, mentorUser=obj.user, name='test')
    obj.oldTeamStudent = Student(team=obj.oldEventTeam,firstName='test',lastName='old',yearLevel=1,gender='Male',birthday=datetime.datetime.now().date())
    
    obj.newEventTeam = Team.objects.create(event=obj.newEvent, division=obj.division, school=obj.newSchool, mentorUser=obj.user, name='test new team')
    obj.newTeamStudent = Student(team=obj.newEventTeam,firstName='test',lastName='thisisastringfortesting',yearLevel=1,gender='Male',birthday=datetime.datetime.now().date())

    login = obj.client.login(request=HttpRequest(), username=obj.username, password=obj.password) 

class TestTeamCreate(TestCase): #TODO more comprehensive tests, check teams actually saved to db properly
    def setUp(self):
        commonSetUp(self)
        self.hardware = HardwarePlatform.objects.create(name='Hardware 1')
        self.software = SoftwarePlatform.objects.create(name='Software 1')

    def testOpenRegoDoesLoad(self):
        response = self.client.get(reverse('teams:create',kwargs={'eventID':self.newEvent.id}))
        self.assertEqual(200, response.status_code)

    def testCancelButtonCorrectLink(self):
        response = self.client.get(reverse('teams:create',kwargs={'eventID':self.newEvent.id}))
        self.assertContains(response, f'href = "/events/{self.newEvent.id}"')

    def testNotPublished_denied_get(self):
        self.newEvent.status = "draft"
        self.newEvent.save()

        response = self.client.get(reverse('teams:create',kwargs={'eventID':self.newEvent.id}))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Event is not published', status_code=403)

    def testClosedRegoReturnsError_get(self):
        response = self.client.get(reverse('teams:create', kwargs={'eventID':self.oldEvent.id}))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Registration has closed for this event', status_code=403)

    def testWorkshopReturnsError_get(self):
        self.newEvent.eventType = 'workshop'
        self.newEvent.save()

        response = self.client.get(reverse('teams:create', kwargs={'eventID':self.newEvent.id}))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Teams/ attendees cannot be created for this event type', status_code=403)

    # This test needs to be a POST request to properly test max team members submission - see issue #368
    # Test fails due to dynamic formsets
    # def testMaxSubmissionNumber(self):
    #     response = self.client.get(reverse('teams:create',kwargs={'eventID':self.newEvent.id}))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response,'First name', self.newEvent.maxMembersPerTeam)

    def testWorkingTeamCreate(self):
        numberTeams = Team.objects.count()
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test+team",
            "division":self.division.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"test",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"1",
            "student_set-0-birthday":"1111-11-11",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:create',kwargs={'eventID':self.newEvent.id}),data=payload,follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/events/{self.newEvent.id}")
        self.assertEqual(Team.objects.count(), numberTeams+1)

    def testWorkingTeamCreate_addAnother(self):
        numberTeams = Team.objects.count()
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test+team",
            "division":self.division.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'add_text': 'blah',
            "student_set-0-firstName":"test",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"1",
            "student_set-0-birthday":"1111-11-11",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.newEvent.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/teams/create/{self.newEvent.id}")
        self.assertEqual(Team.objects.count(), numberTeams+1)

    def testInvalidTeamCreate_badStudent(self):
        numberTeams = Team.objects.count()
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test+team",
            "division":self.division.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"test",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"test",
            "student_set-0-birthday":"1111-11-11",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:create',kwargs={'eventID':self.newEvent.id}),data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Team.objects.count(), numberTeams)

    def testInvalidTeamCreate_existingName(self):
        Team.objects.create(event=self.newEvent, mentorUser=self.user, name='Test', division=self.division)
        numberTeams = Team.objects.count()
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"Test",
            "division":self.division.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"test",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"5",
            "student_set-0-birthday":"1111-11-11",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:create',kwargs={'eventID':self.newEvent.id}),data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Team with this name in this event already exists')
        self.assertEqual(Team.objects.count(), numberTeams)

    def testInvalidTeamCreate_closed(self):
        numberTeams = Team.objects.count()
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"Testnew",
            "division":self.division.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"test",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"5",
            "student_set-0-birthday":"1111-11-11",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:create',kwargs={'eventID':self.oldEvent.id}),data=payload)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Registration has closed for this event', status_code=403)
        self.assertEqual(Team.objects.count(), numberTeams)

class TestTeamDetails(TestCase):
    def setUp(self):
        commonSetUp(self)
        self.hardware = HardwarePlatform.objects.create(name='Hardware 1')
        self.software = SoftwarePlatform.objects.create(name='Software 1')

    def testOpenRegistrationDoesLoad(self):
        response = self.client.get(reverse('teams:details',kwargs={'teamID':self.newEventTeam.id}))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Viewing team test new team")

    def testClosedRegistrationDoesLoad(self):
        response = self.client.get(reverse('teams:details', kwargs={'teamID':self.oldEventTeam.id}))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'Viewing team test')

    def testOpenRegistration_editButton(self):
        response = self.client.get(reverse('teams:details',kwargs={'teamID':self.newEventTeam.id}))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, f'<a href = "/teams/{self.newEventTeam.id}/edit"')

    def testClosedRegistration_noEditButton(self):
        response = self.client.get(reverse('teams:details', kwargs={'teamID':self.oldEventTeam.id}))
        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, "Edit")

    def testOpenRegistration_backEventButton(self):
        response = self.client.get(reverse('teams:details',kwargs={'teamID':self.newEventTeam.id}))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, f'<a href = "/events/{self.newEvent.id}')

    def testClosedRegistration_backEventButton(self):
        response = self.client.get(reverse('teams:details', kwargs={'teamID':self.oldEventTeam.id}))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, f'<a href = "/events/{self.oldEventWithTeams.id}')

class TestTeamEdit(TestCase):
    def setUp(self):
        commonSetUp(self)
        self.hardware = HardwarePlatform.objects.create(name='Hardware 1')
        self.software = SoftwarePlatform.objects.create(name='Software 1')

    def testOpenEditDoesLoad(self):
        response = self.client.get(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id}))
        self.assertEqual(200, response.status_code)

    def testCancelButtonCorrectLink_fromEvent(self):
        response = self.client.get(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id})+ "?fromEvent")
        self.assertContains(response, f'href = "/events/{self.newEvent.id}"')

    def testCancelButtonCorrectLink_fromDetails(self):
        response = self.client.get(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id}))
        self.assertContains(response, f'href = "/teams/{self.newEventTeam.id}"')

    def testNotPublished_denied_get(self):
        self.newEvent.status = "draft"
        self.newEvent.save()

        response = self.client.get(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id}))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Event is not published', status_code=403)

    def testClosedEditReturnsError_get(self):
        response = self.client.get(reverse('teams:edit', kwargs={'teamID':self.oldEventTeam.id}))
        self.assertEqual(403, response.status_code)
        self.assertContains(response, 'Registration has closed for this event', status_code=403)

    def testClosedEditReturnsError_post(self):
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test+team",
            "division":self.division.id,
            "school":self.newSchool.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"teststringhere",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"1",
            "student_set-0-birthday":"1111-11-11",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:edit', kwargs={'teamID':self.oldEventTeam.id}),data=payload)

        self.assertEqual(403, response.status_code)
        self.assertContains(response, 'Registration has closed for this event', status_code=403)

    def testEditStudentSucceeds(self):
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test+team",
            "division":self.division.id,
            "school":self.newSchool.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"teststringhere",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"1",
            "student_set-0-birthday":"1111-11-11",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:edit', kwargs={'teamID':self.newEventTeam.id}),data=payload)
        self.assertEquals(Student.objects.get(firstName="teststringhere").firstName,"teststringhere")
        self.assertEquals(response.status_code, 302)
        self.assertEqual(response.url, f"/teams/{self.newEventTeam.id}")

    def testMissingManagementFormData(self):
        payload = {
            "name":"test+team",
            "division":self.division.id,
            "school":self.newSchool.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"teststringhere",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"1",
            "student_set-0-birthday":"1111-11-11",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:edit', kwargs={'teamID':self.newEventTeam.id}),data=payload)
        self.assertEquals(response.status_code, 400)
        self.assertContains(response, 'Form data missing', status_code=400)

    def testEditStudentWithInvalidFails(self):
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test+team",
            "division":self.division.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"test2",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"test",
            "student_set-0-birthday":"1111-11-11",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id}),data=payload)
        self.assertEqual(200,response.status_code)

def newCommonSetUp(self):
        self.user1 = User.objects.create_user(email=self.email1, password=self.password)

        self.state1 = State.objects.create(typeRegistration=True, name='Victoria', abbreviation='VIC')
        self.state2 = State.objects.create(typeRegistration=True, name='NSW', abbreviation='NSW')
        self.region1 = Region.objects.create(name='Test Region', description='test desc')

        self.user2 = User.objects.create_user(email=self.email2, password=self.password, homeState=self.state1)
        self.user3 = User.objects.create_user(email=self.email3, password=self.password)
        self.superUser = User.objects.create_user(email=self.email_superUser, password=self.password, is_superuser=True, is_staff=True)

        self.school1 = School.objects.create(name='School 1', abbreviation='sch1', state=self.state1, region=self.region1)
        self.school2 = School.objects.create(name='School 2', abbreviation='sch2', state=self.state1, region=self.region1)
        self.school3 = School.objects.create(name='School 3', abbreviation='sch3', state=self.state2, region=self.region1)

        self.campus1 = Campus.objects.create(school=self.school1, name='Campus 1')
        self.campus2 = Campus.objects.create(school=self.school1, name='Campus 2')

        self.year = Year.objects.create(year=2020)
        self.event = Event.objects.create(
            year=self.year,
            state=self.state1,
            name='Test event 1',
            eventType='competition',
            status='published',
            maxMembersPerTeam=5,
            entryFeeIncludesGST=True,
            event_billingType='team',
            event_defaultEntryFee = 50,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date(),
            directEnquiriesTo = self.user1,
        )
        self.division1 = Division.objects.create(name='Division 1')
        self.division2 = Division.objects.create(name='Division 2')
        self.division3 = Division.objects.create(name='Division 3')
        self.division4 = Division.objects.create(name='Division 4', state=self.state2)

        self.invoiceSettings = InvoiceGlobalSettings.objects.create(
            invoiceFromName='From Name',
            invoiceFromDetails='Test Details Text',
            invoiceFooterMessage='Test Footer Text',
        )

class TestTeamDetailsPermissions(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.team2 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 2', division=self.division1)
        self.team3 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 3', division=self.division1, school=self.school1)

    def testLoginRequired(self):
        url = reverse('teams:details', kwargs={'teamID':self.team1.id})
    
        response = self.client.post(url, follow=True)
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/teams/{self.team1.id}")
        self.assertEqual(response.status_code, 302)

    def testLoads_independent(self):
        url = reverse('teams:details', kwargs={'teamID':self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def testDenied_notPublished(self):
        self.event.status = 'draft'
        self.event.save()

        url = reverse('teams:details', kwargs={'teamID':self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Event is not published', status_code=403)

    def testDenied_independent(self):
        url = reverse('teams:details', kwargs={'teamID':self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email2, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'You are not an administrator of this team', status_code=403)

    def testDenied_independent_teamHasSchool(self):
        url = reverse('teams:details', kwargs={'teamID':self.team3.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'You are not an administrator of this team', status_code=403)

    def testLoads_school(self):
        url = reverse('teams:details', kwargs={'teamID':self.team3.id})
        login = self.client.login(request=HttpRequest(), username=self.email3, password=self.password)
        SchoolAdministrator.objects.create(school=self.school1, user=self.user3)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def testDenied_school_noSchool(self):
        url = reverse('teams:details', kwargs={'teamID':self.team3.id})
        login = self.client.login(request=HttpRequest(), username=self.email3, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'You are not an administrator of this team', status_code=403)

    def testDenied_school_wrongSchool(self):
        url = reverse('teams:details', kwargs={'teamID':self.team3.id})
        login = self.client.login(request=HttpRequest(), username=self.email3, password=self.password)
        SchoolAdministrator.objects.create(school=self.school2, user=self.user3)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'You are not an administrator of this team', status_code=403)

class TestTeamEditPermissions(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.team2 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 2', division=self.division1)
        self.team3 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 3', division=self.division1, school=self.school1)

    def testLoginRequired(self):
        url = reverse('teams:edit', kwargs={'teamID':self.team1.id})
    
        response = self.client.post(url, follow=True)
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/teams/{self.team1.id}/edit")
        self.assertEqual(response.status_code, 302)

    def testLoads_independent(self):
        url = reverse('teams:edit', kwargs={'teamID':self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def testDenied_independent(self):
        url = reverse('teams:edit', kwargs={'teamID':self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email2, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'You are not an administrator of this team', status_code=403)

    def testDenied_independent_teamHasSchool(self):
        url = reverse('teams:edit', kwargs={'teamID':self.team3.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'You are not an administrator of this team', status_code=403)

    def testLoads_school(self):
        url = reverse('teams:edit', kwargs={'teamID':self.team3.id})
        login = self.client.login(request=HttpRequest(), username=self.email3, password=self.password)
        SchoolAdministrator.objects.create(school=self.school1, user=self.user3)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def testDenied_school_noSchool(self):
        url = reverse('teams:edit', kwargs={'teamID':self.team3.id})
        login = self.client.login(request=HttpRequest(), username=self.email3, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'You are not an administrator of this team', status_code=403)

    def testDenied_school_wrongSchool(self):
        url = reverse('teams:edit', kwargs={'teamID':self.team3.id})
        login = self.client.login(request=HttpRequest(), username=self.email3, password=self.password)
        SchoolAdministrator.objects.create(school=self.school2, user=self.user3)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'You are not an administrator of this team', status_code=403)

class TestTeamDelete(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.team2 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 2', division=self.division1)
        self.team3 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 3', division=self.division1, school=self.school1)

    def testLoginRequired(self):
        url = reverse('teams:edit', kwargs={'teamID':self.team1.id})
    
        response = self.client.delete(url, follow=True)
        self.assertContains(response, "Login")

        response = self.client.delete(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/teams/{self.team1.id}/edit")
        self.assertEqual(response.status_code, 302)

    def testDenied_independent(self):
        url = reverse('teams:edit', kwargs={'teamID':self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email2, password=self.password)
    
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'You are not an administrator of this team', status_code=403)
        Team.objects.get(pk=self.team1.pk)

    def testDenied_independent_teamHasSchool(self):
        url = reverse('teams:edit', kwargs={'teamID':self.team3.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'You are not an administrator of this team', status_code=403)
        Team.objects.get(pk=self.team3.pk)

    def testDenied_school_noSchool(self):
        url = reverse('teams:edit', kwargs={'teamID':self.team3.id})
        login = self.client.login(request=HttpRequest(), username=self.email3, password=self.password)
    
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'You are not an administrator of this team', status_code=403)
        Team.objects.get(pk=self.team3.pk)

    def testDenied_school_wrongSchool(self):
        url = reverse('teams:edit', kwargs={'teamID':self.team3.id})
        login = self.client.login(request=HttpRequest(), username=self.email3, password=self.password)
        SchoolAdministrator.objects.create(school=self.school2, user=self.user3)
    
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'You are not an administrator of this team', status_code=403)
        Team.objects.get(pk=self.team3.pk)

    def testSuccess(self):
        Team.objects.get(pk=self.team1.pk)
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        url = reverse('teams:edit', kwargs={'teamID':self.team1.id})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertRaises(Team.DoesNotExist, lambda: Team.objects.get(pk=self.team1.pk))

    def testWrongEndpointDenied(self):
        Team.objects.get(pk=self.team1.pk)
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        url = reverse('teams:create', kwargs={'eventID':self.team1.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
        Team.objects.get(pk=self.team1.pk)

    def testDenied_closed(self):
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
        self.event.save()
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        url = reverse('teams:edit', kwargs={'teamID':self.team1.id})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Registration has closed for this event', status_code=403)
        Team.objects.get(pk=self.team1.pk)

class TestTeamClean(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)
        self.team1 = Team(event=self.event, mentorUser=self.user1, school=self.school1, name='Team 1', division=self.division1)
        self.team2 = Team(event=self.event, mentorUser=self.user1, school=self.school2, name='Team 2', division=self.division1)
        self.schoolAdmin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user1)
        self.schoolAdmin2 = SchoolAdministrator.objects.create(school=self.school2, user=self.user1)

    def testWrongEventType(self):
        self.event.eventType = 'workshop'
        self.event.save()

        self.assertRaises(ValidationError, self.team1.clean)

    def testNoCampus(self):
        self.assertEqual(self.team1.clean(), None)

    def testCampusValid(self):
        self.team1.campus = self.campus1
        self.assertEqual(self.team1.clean(), None)

    def testCampusWrongSchool(self):
        self.team2.campus = self.campus1
        self.assertRaises(ValidationError, self.team2.clean)

    def testDivisionWrongState(self):
        self.team1.division = self.division4
        self.assertRaises(ValidationError, self.team1.clean)     

    def testCheckMentorIsAdminOfSchool_noSchool(self):
        self.team3 = Team(event=self.event, mentorUser=self.user1, name='Team 3', division=self.division1)
        self.assertEqual(self.team3.clean(), None)

    def testCheckMentorIsAdminOfSchool(self):
        self.team3 = Team(event=self.event, mentorUser=self.user1, school=self.school1, name='Team 3', division=self.division1)
        self.assertEqual(self.team3.clean(), None)

    def testCheckMentorIsAdminOfSchool_existing(self):
        self.schoolAdmin1.delete()
        self.team3 = Team.objects.create(event=self.event, mentorUser=self.user1, school=self.school1, name='Team 3', division=self.division1)
        self.assertEqual(self.team3.clean(), None)

    def testCheckMentorIsAdminOfSchool_notAdmin(self):
        self.schoolAdmin1.delete()
        self.team3 = Team(event=self.event, mentorUser=self.user1, school=self.school1, name='Team 3', division=self.division1)
        self.assertRaises(ValidationError, self.team3.clean)

class TestInvoiceMethods(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)

    def testCampusInvoicingDisabled_noSchool(self):
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.assertEqual(self.team1.campusInvoicingEnabled(), False)

    def testCampusInvoicingDisabled(self):
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, school=self.school1, name='Team 1', division=self.division1)
        self.assertEqual(self.team1.campusInvoicingEnabled(), False)

    def testCampusInvoicingEnabled(self):
        self.invoice1 = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1, campus=self.campus1)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, school=self.school1, name='Team 1', division=self.division1)
        self.assertEqual(self.team1.campusInvoicingEnabled(), True)

    def testSave_NoSchool_NoExistingInvoice(self):
        self.assertEqual(Invoice.objects.filter(event=self.event, invoiceToUser=self.user1, school=None).count(), 0)

        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.assertEqual(Invoice.objects.filter(event=self.event, invoiceToUser=self.user1, school=None).count(), 1)

    def testSave_NoSchool_ExistingInvoice(self):
        self.invoice1 = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=None)
        self.assertEqual(Invoice.objects.filter(event=self.event, invoiceToUser=self.user1, school=None).count(), 1)

        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.assertEqual(Invoice.objects.filter(event=self.event, invoiceToUser=self.user1, school=None).count(), 1)

    def testSave_CampusInvoicingDisabled_NoExistingInvoice(self):
        self.assertEqual(Invoice.objects.filter(event=self.event, invoiceToUser=self.user1, school=self.school1).count(), 0)

        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, school=self.school1, name='Team 1', division=self.division1)
        self.assertEqual(Invoice.objects.filter(event=self.event, invoiceToUser=self.user1, school=self.school1).count(), 1)

    def testSave_CampusInvoicingDisabled_ExistingInvoice(self):
        self.invoice1 = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1)
        self.assertEqual(Invoice.objects.filter(event=self.event, invoiceToUser=self.user1, school=self.school1).count(), 1)

        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, school=self.school1, name='Team 1', division=self.division1)
        self.assertEqual(Invoice.objects.filter(event=self.event, invoiceToUser=self.user1, school=self.school1).count(), 1)

    def testSave_CampusInvoicingEnabled_NoExistingInvoice(self):
        self.invoice1 = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1, campus=self.campus1)

        self.assertEqual(Invoice.objects.filter(event=self.event, invoiceToUser=self.user1, school=self.school1, campus=self.campus2).count(), 0)

        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, school=self.school1, campus=self.campus2, name='Team 1', division=self.division1)
        self.assertEqual(Invoice.objects.filter(event=self.event, invoiceToUser=self.user1, school=self.school1, campus=self.campus2).count(), 1)

    def testSave_CampusInvoicingEnabled_ExistingInvoice(self):
        self.invoice1 = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1, campus=self.campus1)
        self.invoice2 = Invoice.objects.create(event=self.event, invoiceToUser=self.user1, school=self.school1, campus=self.campus2)

        self.assertEqual(Invoice.objects.filter(event=self.event, invoiceToUser=self.user1, school=self.school1, campus=self.campus2).count(), 1)

        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, school=self.school1, campus=self.campus2, name='Team 1', division=self.division1)
        self.assertEqual(Invoice.objects.filter(event=self.event, invoiceToUser=self.user1, school=self.school1, campus=self.campus2).count(), 1)

class TestTeamMethods(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user2, name='Team 1', division=self.division1)
        self.team2 = Team.objects.create(event=self.event, mentorUser=self.user2, name='Team 2', school=self.school2, division=self.division1)
        self.team3 = Team.objects.create(event=self.event, mentorUser=self.user2, name='Team 3', school=self.school3, division=self.division1)
        self.user2.first_name = 'First'
        self.user2.last_name = 'Last'
        self.user2.save()

    def testGetState(self):
        self.assertEqual(self.team1.getState(), self.state1)

    def testHomeState_school(self):
        self.assertEqual(self.team3.homeState(), self.state2)

    def testHomeState_noSchool(self):
        self.assertEqual(self.team1.homeState(), self.state1)

    def testEventAttendanceType(self):
        self.assertEqual(self.team1.eventAttendanceType(), 'team')

    def testChildObject(self):
        self.assertEqual(self.team1.childObject(), self.team1)

    def testMentorUserName(self):
        self.assertEqual(self.team1.mentorUserName(), 'First Last')

    def testMentorUserEmail(self):
        self.assertEqual(self.team1.mentorUserEmail(), self.email2)

class TestTeamCreationFormValidation_School(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)
        self.availableDivision = AvailableDivision.objects.create(division=self.division1, event=self.event)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, school=self.school1, name='Team 1', division=self.division1)
        self.team2 = Team.objects.create(event=self.event, mentorUser=self.user2, school=self.school2, name='Team 2', division=self.division1)
        self.admin1 = SchoolAdministrator.objects.create(school=self.school1, user=self.user1)
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        self.schoolAssertValue = self.school1

        self.hardware = HardwarePlatform.objects.create(name='Hardware 1')
        self.software = SoftwarePlatform.objects.create(name='Software 1')

    def testValidCreate(self):
        self.assertEqual(self.user1.currentlySelectedSchool, self.schoolAssertValue)
        payload = {
            'student_set-TOTAL_FORMS':0,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "name":"Team+8",
            "division":self.division1.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Team.objects.filter(school=self.schoolAssertValue).count(), 2)

    def testInValidCreate_schoolEventMax(self):
        self.assertEqual(self.user1.currentlySelectedSchool, self.schoolAssertValue)
        self.event.event_maxTeamsPerSchool = 1
        self.event.save()

        payload = {
            'student_set-TOTAL_FORMS':0,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "name":"Team+3",
            "division":self.division1.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Max teams for school for this event exceeded. Contact the organiser.")
        self.assertEqual(Team.objects.filter(school=self.schoolAssertValue).count(), 1)
        self.assertEqual(Team.objects.filter(event=self.event).count(), 2)

    def testInValidCreate_overallEventMax(self):
        self.assertEqual(self.user1.currentlySelectedSchool, self.schoolAssertValue)
        self.event.event_maxTeamsForEvent = 2
        self.event.save()

        payload = {
            'student_set-TOTAL_FORMS':0,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "name":"Team+3",
            "division":self.division1.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Max teams for this event exceeded. Contact the organiser.")
        self.assertEqual(Team.objects.filter(school=self.schoolAssertValue).count(), 1)
        self.assertEqual(Team.objects.filter(event=self.event).count(), 2)

    def testInValidCreate_schoolDivisionMax(self):
        self.assertEqual(self.user1.currentlySelectedSchool, self.schoolAssertValue)
        self.availableDivision.division_maxTeamsPerSchool = 1
        self.availableDivision.save()

        payload = {
            'student_set-TOTAL_FORMS':0,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "name":"Team+3",
            "division":self.division1.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Max teams for school for this event division exceeded. Contact the organiser.")
        self.assertEqual(Team.objects.filter(school=self.schoolAssertValue).count(), 1)
        self.assertEqual(Team.objects.filter(event=self.event).count(), 2)

    def testInValidCreate_overallDivisionMax(self):
        self.assertEqual(self.user1.currentlySelectedSchool, self.schoolAssertValue)
        self.availableDivision.division_maxTeamsForDivision = 2
        self.availableDivision.save()

        payload = {
            'student_set-TOTAL_FORMS':0,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "name":"Team+3",
            "division":self.division1.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Max teams for this event division exceeded. Contact the organiser.")
        self.assertEqual(Team.objects.filter(school=self.schoolAssertValue).count(), 1)
        self.assertEqual(Team.objects.filter(event=self.event).count(), 2)

    def testInValidCreate_division(self):
        self.assertEqual(self.user1.currentlySelectedSchool, self.schoolAssertValue)
        payload = {
            'student_set-TOTAL_FORMS':0,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "name":"Team+3",
            "division":self.division2.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Division: Select a valid choice. That choice is not one of the available choices.")
        self.assertEqual(Team.objects.filter(school=self.schoolAssertValue).count(), 1)

    def testInValidCreate_divisionMissing(self):
        self.assertEqual(self.user1.currentlySelectedSchool, self.schoolAssertValue)
        payload = {
            'student_set-TOTAL_FORMS':0,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "name":"Team+3",
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Required field is missing")
        self.assertEqual(Team.objects.filter(school=self.schoolAssertValue).count(), 1)

class TestTeamCreationFormValidation_Independent(TestTeamCreationFormValidation_School):
    def setUp(self):
        newCommonSetUp(self)
        self.availableDivision = AvailableDivision.objects.create(division=self.division1, event=self.event)
        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.team2 = Team.objects.create(event=self.event, mentorUser=self.user2, school=self.school2, name='Team 2', division=self.division1)
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        self.schoolAssertValue = None

        self.hardware = HardwarePlatform.objects.create(name='Hardware 1')
        self.software = SoftwarePlatform.objects.create(name='Software 1')

def createEventsAndTeams(self):
    self.event1 = Event.objects.create(
        year=self.year,
        state=self.state1,
        name='Event 1',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        entryFeeIncludesGST=True,
        event_billingType='team',
        event_defaultEntryFee = 50,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date(),
        directEnquiriesTo = self.user1,
    )
    self.event2 = Event.objects.create(
        year=self.year,
        state=self.state2,
        name='Event 2',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        entryFeeIncludesGST=True,
        event_billingType='team',
        event_defaultEntryFee = 50,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=5)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date(),
        directEnquiriesTo = self.user1,
    )
    self.team1 = Team.objects.create(event=self.event1, mentorUser=self.user2, name='Team 1', division=self.division1)
    self.team2 = Team.objects.create(event=self.event2, mentorUser=self.user2, name='Team 2', division=self.division1)

class TestTeamAdmin(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    emailsuper = 'user4@user.com'
    email_superUser = emailsuper
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)
        createEventsAndTeams(self)
        self.coord1 = Coordinator.objects.create(user=self.user1, state=self.state1, permissions='full', position='Thing')
        self.coord2 = Coordinator.objects.create(user=self.user2, state=self.state2, permissions='full', position='Thing')

        self.hardware = HardwarePlatform.objects.create(name='Hardware 1')
        self.software = SoftwarePlatform.objects.create(name='Software 1')

    def testListLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:teams_team_changelist'))
        self.assertEqual(response.status_code, 200)

    def testChangeLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:teams_team_change', args=(self.team1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testListContent_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:teams_team_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Team 1')
        self.assertContains(response, 'Team 2')

    def testDeleteLoads_superuser(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:teams_team_delete', args=(self.team1.id,)))
        self.assertEqual(response.status_code, 200)

    def testListNonStaff_denied(self):
        self.client.login(request=HttpRequest(), username=self.email3, password=self.password)
        response = self.client.get(reverse('admin:teams_team_changelist'))
        self.assertEqual(response.status_code, 302)

    def testListLoads_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:teams_team_changelist'))
        self.assertEqual(response.status_code, 200)

    def testListContent_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:teams_team_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Team 1')
        self.assertNotContains(response, 'Team 2')

    def testChangeLoads_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:teams_team_change', args=(self.team1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save')

    def testChangeDenied_wrongState_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:teams_team_change', args=(self.team2.id,)))
        self.assertEqual(response.status_code, 302)

    def testViewLoads_viewPermission_coordinator(self):
        self.coord1.permissions = 'viewall'
        self.coord1.save()

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        response = self.client.get(reverse('admin:teams_team_change', args=(self.team1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Save')

    # Form contents

    def testChangeContent(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:teams_team_change', args=(self.team1.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Campus:')
        self.assertNotContains(response, 'You can select campus after you have clicked save.')

    def testAddContent(self):
        self.client.login(request=HttpRequest(), username=self.emailsuper, password=self.password)
        response = self.client.get(reverse('admin:teams_team_add'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Campus:')
        self.assertContains(response, 'You can select campus after you have clicked save.')

    # Change Post

    def testChangePostAllowed_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'event': self.event1.id,
            'division': self.division1.id,
            'mentorUser': self.user2.id,
            'school': '',
            'campus': '',
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'student_set-TOTAL_FORMS': 0,
            'student_set-INITIAL_FORMS': 0,
            'student_set-MIN_NUM_FORMS': 0,
            'student_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:teams_team_change', args=(self.team1.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('admin:teams_team_change', args=(self.team1.id,)), data=payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'was changed successfully')

        self.team1.refresh_from_db()
        self.assertEqual(self.team1.name, 'Renamed 1')

    def testChangePostDenied_wrongState_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 2',
            'event': self.event2.id,
            'division': self.division1.id,
            'mentorUser': self.user2.id,
            'school': '',
            'campus': '',
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'student_set-TOTAL_FORMS': 0,
            'student_set-INITIAL_FORMS': 0,
            'student_set-MIN_NUM_FORMS': 0,
            'student_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:teams_team_change', args=(self.team2.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('admin:teams_team_change', args=(self.team2.id,)), data=payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'doesn’t exist. Perhaps it was deleted?')

        self.team2.refresh_from_db()
        self.assertEqual(self.team2.name, 'Team 2')

    def testChangePostDenied_viewPermission_coordinator(self):
        self.coord1.permissions = 'viewall'
        self.coord1.save()

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'event': self.event1.id,
            'division': self.division1.id,
            'mentorUser': self.user2.id,
            'school': '',
            'campus': '',
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'student_set-TOTAL_FORMS': 0,
            'student_set-INITIAL_FORMS': 0,
            'student_set-MIN_NUM_FORMS': 0,
            'student_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:teams_team_change', args=(self.team1.id,)), data=payload)
        self.assertEqual(response.status_code, 403)

        self.team1.refresh_from_db()
        self.assertEqual(self.team1.name, 'Team 1')

    # Add post

    def testAddPostAllowed_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'New Team',
            'event': self.event1.id,
            'division': self.division1.id,
            'mentorUser': self.user2.id,
            'school': '',
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'student_set-TOTAL_FORMS': 0,
            'student_set-INITIAL_FORMS': 0,
            'student_set-MIN_NUM_FORMS': 0,
            'student_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:teams_team_add'), data=payload, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Team.objects.filter(name='New Team').exists(), True)
        self.assertContains(response, 'was added successfully. You may edit it again below.')

    def testAddPostDenied_viewPermission_coordinator(self):
        self.coord1.permissions = 'viewall'
        self.coord1.save()

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'New Team',
            'event': self.event1.id,
            'division': self.division1.id,
            'mentorUser': self.user2.id,
            'school': '',
            'student_set-TOTAL_FORMS': 0,
            'student_set-INITIAL_FORMS': 0,
            'student_set-MIN_NUM_FORMS': 0,
            'student_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:teams_team_add'), data=payload, follow=True)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Team.objects.filter(name='New Team').exists(), False)

    # Event FK filtering

    # homeState field
    def testEventFieldSuccess_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'event': self.event1.id,
            'division': self.division1.id,
            'mentorUser': self.user2.id,
            'school': '',
            'campus': '',
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'student_set-TOTAL_FORMS': 0,
            'student_set-INITIAL_FORMS': 0,
            'student_set-MIN_NUM_FORMS': 0,
            'student_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:teams_team_change', args=(self.team1.id,)), data=payload)
        self.assertEqual(response.status_code, 302)

    def testEventFieldDenied_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'event': self.event2.id,
            'division': self.division1.id,
            'mentorUser': self.user2.id,
            'school': '',
            'campus': '',
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'student_set-TOTAL_FORMS': 0,
            'student_set-INITIAL_FORMS': 0,
            'student_set-MIN_NUM_FORMS': 0,
            'student_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:teams_team_change', args=(self.team1.id,)), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'Select a valid choice. That choice is not one of the available choices.')

    def testEventFieldBlankDenied_coordinator(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'Renamed 1',
            'event': '',
            'division': self.division1.id,
            'mentorUser': self.user2.id,
            'school': '',
            'campus': '',
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'student_set-TOTAL_FORMS': 0,
            'student_set-INITIAL_FORMS': 0,
            'student_set-MIN_NUM_FORMS': 0,
            'student_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:teams_team_change', args=(self.team1.id,)), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, 'This field is required.')

    # Test admin validation

    def testMultipleSchoolsDenied_schoolBlank(self):
        SchoolAdministrator.objects.create(user=self.user2, school=self.school1)
        SchoolAdministrator.objects.create(user=self.user2, school=self.school2)

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'New Team',
            'event': self.event1.id,
            'division': self.division1.id,
            'mentorUser': self.user2.id,
            'school': '',
            'campus': '',
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'student_set-TOTAL_FORMS': 0,
            'student_set-INITIAL_FORMS': 0,
            'student_set-MIN_NUM_FORMS': 0,
            'student_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:teams_team_add'), data=payload, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, f"School must not be blank because {self.user2.fullname_or_email()} is an administrator of multiple schools. Please select a school.")

        self.assertEqual(Team.objects.filter(name='New Team').exists(), False)

    def testMultipleSchoolsSuccess_schoolNotBlank(self):
        SchoolAdministrator.objects.create(user=self.user2, school=self.school1)
        SchoolAdministrator.objects.create(user=self.user2, school=self.school2)

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'New Team',
            'event': self.event1.id,
            'division': self.division1.id,
            'mentorUser': self.user2.id,
            'school': self.school1.id,
            'campus': '',
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'student_set-TOTAL_FORMS': 0,
            'student_set-INITIAL_FORMS': 0,
            'student_set-MIN_NUM_FORMS': 0,
            'student_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:teams_team_add'), data=payload, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'was added successfully. You may edit it again below.')

        self.assertEqual(Team.objects.filter(name='New Team').exists(), True)

    def testNotAdminOfSchool(self):
        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'New Team',
            'event': self.event1.id,
            'division': self.division1.id,
            'mentorUser': self.user2.id,
            'school': self.school1.id,
            'campus': '',
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'student_set-TOTAL_FORMS': 0,
            'student_set-INITIAL_FORMS': 0,
            'student_set-MIN_NUM_FORMS': 0,
            'student_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:teams_team_add'), data=payload, follow=True)

        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, f"is not an administrator of")

        self.assertEqual(Team.objects.filter(name='New Team').exists(), False)

    def testRemoveSchoolDenied(self):
        SchoolAdministrator.objects.create(user=self.user2, school=self.school1)
        SchoolAdministrator.objects.create(user=self.user2, school=self.school2)
        team3 = Team.objects.create(name='Team 3', event=self.event1, division=self.division1, mentorUser=self.user2, school=self.school1)

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'New Team',
            'event': self.event1.id,
            'division': self.division1.id,
            'mentorUser': self.user2.id,
            'school': '',
            'campus': '',
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'student_set-TOTAL_FORMS': 0,
            'student_set-INITIAL_FORMS': 0,
            'student_set-MIN_NUM_FORMS': 0,
            'student_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:teams_team_change', args=(team3.id,)), data=payload, follow=True)

        self.assertContains(response, 'Please correct the error below.')
        self.assertContains(response, f"remove {self.school1} from this team while {self.user2.fullname_or_email()} is still an admin of this school.")

        team3.refresh_from_db()
        self.assertEqual(team3.school, self.school1)

    # Test auto school set
    def testMultipleSchoolsSuccess_schoolNotBlank(self):
        SchoolAdministrator.objects.create(user=self.user2, school=self.school1)

        self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
        payload = {
            'name': 'New Team',
            'event': self.event1.id,
            'division': self.division1.id,
            'mentorUser': self.user2.id,
            'school': '',
            'campus': '',
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'student_set-TOTAL_FORMS': 0,
            'student_set-INITIAL_FORMS': 0,
            'student_set-MIN_NUM_FORMS': 0,
            'student_set-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(reverse('admin:teams_team_add'), data=payload, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'was added successfully. You may edit it again below.')
        self.assertContains(response, f"(School 1) automatically added to New Team")

        self.assertEqual(Team.objects.filter(name='New Team').exists(), True)
        self.assertEqual(Team.objects.get(name='New Team').school, self.school1)
