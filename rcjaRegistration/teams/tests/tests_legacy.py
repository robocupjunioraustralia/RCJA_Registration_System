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
from teams.models import Team, Student, HardwarePlatform, SoftwarePlatform

from teams.forms import TeamForm

import datetime
# Create your tests here.

def commonSetUp(obj): #copied from events, todo refactor
    obj.username = 'user@user.com'
    obj.password = 'password'
    obj.user = user = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=obj.username, password=obj.password)
    obj.newState = State.objects.create(
        typeCompetition=True, typeUserRegistration=True,
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
    obj.division = Division.objects.create(name='Division 1 Name')

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
        maxMembersPerTeam=2,
        event_defaultEntryFee = 4,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=3)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=4)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-2)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+2)).date(),
        directEnquiriesTo = obj.user     
    )
    obj.newEventAvailableDivision = AvailableDivision.objects.create(division=obj.division, event=obj.newEvent)

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
    
    obj.newEventTeam = Team.objects.create(event=obj.newEvent, division=obj.division, school=obj.newSchool, mentorUser=obj.user, name='test new team')

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
        numberStudents = Student.objects.count()
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test team",
            "division":self.division.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"test",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"1",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:create',kwargs={'eventID':self.newEvent.id}),data=payload,follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/events/{self.newEvent.id}")
        self.assertEqual(Team.objects.count(), numberTeams+1)
        self.assertEqual(Student.objects.count(), numberStudents+1)

    def testWorkingTeamCreate_addAnother(self):
        numberTeams = Team.objects.count()
        numberStudents = Student.objects.count()
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test team",
            "division":self.division.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'add_text': 'blah',
            "student_set-0-firstName":"test",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"1",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.newEvent.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/teams/create/{self.newEvent.id}")
        self.assertEqual(Team.objects.count(), numberTeams+1)
        self.assertEqual(Student.objects.count(), numberStudents+1)

    def testInvalidTeamCreate_badStudent(self):
        numberTeams = Team.objects.count()
        numberStudents = Student.objects.count()
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test team",
            "division":self.division.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"test",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"test",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:create',kwargs={'eventID':self.newEvent.id}),data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Year level: Enter a whole number.")

        self.assertEqual(Team.objects.count(), numberTeams)
        self.assertEqual(Student.objects.count(), numberStudents)

    def testInvalidTeamCreate_existingName(self):
        Team.objects.create(event=self.newEvent, mentorUser=self.user, name='Test', division=self.division)
        numberTeams = Team.objects.count()
        numberStudents = Student.objects.count()
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"Test",
            "division":self.division.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"test",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"5",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:create',kwargs={'eventID':self.newEvent.id}),data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Team with this name in this event already exists')
        self.assertEqual(Team.objects.count(), numberTeams)
        self.assertEqual(Student.objects.count(), numberStudents)

    def testInvalidTeamCreate_illegalCharacterInName(self):
        numberTeams = Team.objects.count()
        numberStudents = Student.objects.count()
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"illegal%",
            "division":self.division.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"test",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"5",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:create',kwargs={'eventID':self.newEvent.id}),data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Name: Contains character that isn&#x27;t allowed. Allowed characters are a-z, A-Z, 0-9, -_ and space.")
        self.assertEqual(Team.objects.count(), numberTeams)
        self.assertEqual(Student.objects.count(), numberStudents)

    def testInvalidTeamCreate_closed(self):
        numberTeams = Team.objects.count()
        numberStudents = Student.objects.count()
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"Testnew",
            "division":self.division.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"test",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"5",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:create',kwargs={'eventID':self.oldEvent.id}),data=payload)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Registration has closed for this event', status_code=403)
        self.assertEqual(Team.objects.count(), numberTeams)
        self.assertEqual(Student.objects.count(), numberStudents)

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

    def testLoadsSchoolEventMaximumReached(self):
        self.newEvent.event_maxTeamsPerSchool = 1
        self.newEvent.save()

        response = self.client.get(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id}))
        self.assertEqual(200, response.status_code)

    def testLoadsOverallEventMaximumReached(self):
        self.newEvent.event_maxTeamsForEvent = 1
        self.newEvent.save()

        response = self.client.get(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id}))
        self.assertEqual(200, response.status_code)

    def testLoadsSchoolDivisionMaximumReached(self):
        self.newEventAvailableDivision.division_maxTeamsPerSchool = 1
        self.newEventAvailableDivision.save()

        response = self.client.get(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id}))
        self.assertEqual(200, response.status_code)

    def testLoadsOverallDivisionMaximumReached(self):
        self.newEventAvailableDivision.division_maxTeamsForDivision = 1
        self.newEventAvailableDivision.save()

        response = self.client.get(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id}))
        self.assertEqual(200, response.status_code)

    def testDivisionQSValidSchoolDivisionMaximumReached(self):
        self.newEventAvailableDivision.division_maxTeamsPerSchool = 1
        self.newEventAvailableDivision.save()

        response = self.client.get(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id}))
        self.assertContains(response, 'Division 1 Name')
        self.assertNotContains(response, 'Division 1 Name: Max teams for school for this event division reached. Contact the organiser if you want to register more teams in this division.')

    def testDivisionQSValidOverallDivisionMaximumReached(self):
        self.newEventAvailableDivision.division_maxTeamsForDivision = 1
        self.newEventAvailableDivision.save()

        response = self.client.get(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id}))
        self.assertContains(response, 'Division 1 Name')
        self.assertNotContains(response, 'Division 1 Name: Max teams for this event division reached. Contact the organiser if you want to register more teams in this division.')

    def testClosedEditReturnsError_post(self):
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test team",
            "division":self.division.id,
            "school":self.newSchool.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"teststringhere",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"1",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:edit', kwargs={'teamID':self.oldEventTeam.id}),data=payload)

        self.assertEqual(403, response.status_code)
        self.assertContains(response, 'Registration has closed for this event', status_code=403)

    def testAddStudentSucceeds(self):
        existingStudents = self.newEventTeam.student_set.count()
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test team",
            "division":self.division.id,
            "school":self.newSchool.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"First 1",
            "student_set-0-lastName":"Last 1",
            "student_set-0-yearLevel":"1",
            "student_set-0-gender":"male",
        }
        response = self.client.post(reverse('teams:edit', kwargs={'teamID':self.newEventTeam.id}),data=payload)
        self.assertEquals(response.status_code, 302)
        self.assertEqual(response.url, f"/teams/{self.newEventTeam.id}")

        self.assertEqual(self.newEventTeam.student_set.count(), existingStudents+1)
        self.assertEquals(Student.objects.get(firstName="First 1").firstName, "First 1")

    def testAdd2StudentsSucceeds(self):
        existingStudents = self.newEventTeam.student_set.count()
        payload = {
            'student_set-TOTAL_FORMS':2,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test team",
            "division":self.division.id,
            "school":self.newSchool.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"First 1",
            "student_set-0-lastName":"Last 1",
            "student_set-0-yearLevel":"1",
            "student_set-0-gender":"male",
            "student_set-1-firstName":"First 2",
            "student_set-1-lastName":"Last 2",
            "student_set-1-yearLevel":"1",
            "student_set-1-gender":"male",
        }
        response = self.client.post(reverse('teams:edit', kwargs={'teamID':self.newEventTeam.id}),data=payload)
        self.assertEquals(response.status_code, 302)
        self.assertEqual(response.url, f"/teams/{self.newEventTeam.id}")

        self.assertEqual(self.newEventTeam.student_set.count(), existingStudents+2)
        self.assertEquals(Student.objects.get(firstName="First 1").firstName, "First 1")
        self.assertEquals(Student.objects.get(firstName="First 2").firstName, "First 2")

    def testAdd3StudentsFails(self):
        existingStudents = self.newEventTeam.student_set.count()
        payload = {
            'student_set-TOTAL_FORMS':3,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test team",
            "division":self.division.id,
            "school":self.newSchool.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"First 1",
            "student_set-0-lastName":"Last 1",
            "student_set-0-yearLevel":"1",
            "student_set-0-gender":"male",
            "student_set-1-firstName":"First 2",
            "student_set-1-lastName":"Last 2",
            "student_set-1-yearLevel":"1",
            "student_set-1-gender":"male",
            "student_set-2-firstName":"First 3",
            "student_set-2-lastName":"Last 3",
            "student_set-2-yearLevel":"1",
            "student_set-2-gender":"male",
        }
        response = self.client.post(reverse('teams:edit', kwargs={'teamID':self.newEventTeam.id}),data=payload)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "Please submit at most 2 forms.")

        self.assertEqual(self.newEventTeam.student_set.count(), existingStudents)
        self.assertRaises(Student.DoesNotExist, lambda: Student.objects.get(firstName="First 1"))

    def testAddStudentOverLimitIgnored_editedTotal(self):
        self.student1 = Student.objects.create(team=self.newEventTeam, firstName='First 1', lastName='Last 1', yearLevel=1, gender='male')
        self.student2 = Student.objects.create(team=self.newEventTeam, firstName='First 2', lastName='Last 2', yearLevel=1, gender='male')
        existingStudents = self.newEventTeam.student_set.count()
        payload = {
            'student_set-TOTAL_FORMS':2,
            "student_set-INITIAL_FORMS":1,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test team",
            "division":self.division.id,
            "school":self.newSchool.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-id": self.student1.id,
            "student_set-0-firstName":"New 1",
            "student_set-0-lastName":"Last 1",
            "student_set-0-yearLevel":"1",
            "student_set-0-gender":"male",
            "student_set-2-firstName":"First 3",
            "student_set-2-lastName":"Last 3",
            "student_set-2-yearLevel":"1",
            "student_set-2-gender":"male",
        }
        response = self.client.post(reverse('teams:edit', kwargs={'teamID':self.newEventTeam.id}),data=payload)
        self.assertEquals(response.status_code, 302)
        self.assertEqual(response.url, f"/teams/{self.newEventTeam.id}")

        self.assertEqual(self.newEventTeam.student_set.count(), existingStudents)
        self.assertEquals(Student.objects.get(firstName="New 1").firstName, "New 1")
        self.assertEquals(Student.objects.get(firstName="First 2").firstName, "First 2")
        self.assertRaises(Student.DoesNotExist, lambda: Student.objects.get(firstName="First 1"))
        self.assertRaises(Student.DoesNotExist, lambda: Student.objects.get(firstName="First 3"))

    def testAddStudentOverLimitFails(self):
        self.student1 = Student.objects.create(team=self.newEventTeam, firstName='First 1', lastName='Last 1', yearLevel=1, gender='male')
        self.student2 = Student.objects.create(team=self.newEventTeam, firstName='First 2', lastName='Last 2', yearLevel=1, gender='male')
        existingStudents = self.newEventTeam.student_set.count()
        payload = {
            'student_set-TOTAL_FORMS':3,
            "student_set-INITIAL_FORMS":2,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test team",
            "division":self.division.id,
            "school":self.newSchool.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-id": self.student1.id,
            "student_set-0-firstName":"New 1",
            "student_set-0-lastName":"Last 1",
            "student_set-0-yearLevel":"1",
            "student_set-0-gender":"male",
            "student_set-2-firstName":"First 3",
            "student_set-2-lastName":"Last 3",
            "student_set-2-yearLevel":"1",
            "student_set-2-gender":"male",
        }
        response = self.client.post(reverse('teams:edit', kwargs={'teamID':self.newEventTeam.id}),data=payload)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "Please submit at most 2 forms.")

        self.assertEqual(self.newEventTeam.student_set.count(), existingStudents)
        self.assertEquals(Student.objects.get(firstName="First 1").firstName, "First 1")
        self.assertEquals(Student.objects.get(firstName="First 2").firstName, "First 2")
        self.assertRaises(Student.DoesNotExist, lambda: Student.objects.get(firstName="New 1"))
        self.assertRaises(Student.DoesNotExist, lambda: Student.objects.get(firstName="First 3"))

    def testMissingManagementFormData(self):
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test team",
            "division":self.division.id,
            "school":self.newSchool.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"teststringhere",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"1",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:edit', kwargs={'teamID':self.newEventTeam.id}),data=payload)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'ManagementForm data is missing or has been tampered with')

    def testMissingManagementFormData_invalidForm(self):
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test team",
            "division":self.division.id,
            "school":self.newSchool.id,
            'hardwarePlatform': 'string',
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"teststringhere",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"1",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:edit', kwargs={'teamID':self.newEventTeam.id}),data=payload)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'ManagementForm data is missing or has been tampered with')

    def testEditStudentWithInvalidFails(self):
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test team",
            "division":self.division.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            "student_set-0-firstName":"test2",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"test",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id}),data=payload)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Year level: Enter a whole number.")

def newCommonSetUp(self):
        self.user1 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email1, password=self.password)

        self.state1 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='Victoria', abbreviation='VIC')
        self.state2 = State.objects.create(typeCompetition=True, typeUserRegistration=True, name='NSW', abbreviation='NSW')
        self.region1 = Region.objects.create(name='Test Region', description='test desc')
        self.region2 = Region.objects.create(name='Test Region2', description='test desc')

        self.user2 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email2, password=self.password, homeState=self.state1, homeRegion=self.region1)
        self.user3 = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email3, password=self.password)
        self.superUser = User.objects.create_user(adminChangelogVersionShown=User.ADMIN_CHANGELOG_CURRENT_VERSION, email=self.email_superUser, password=self.password, is_superuser=True, is_staff=True)

        self.school1 = School.objects.create(name='School 1', abbreviation='sch1', state=self.state1, region=self.region1)
        self.school2 = School.objects.create(name='School 2', abbreviation='sch2', state=self.state1, region=self.region1)
        self.school3 = School.objects.create(name='School 3', abbreviation='sch3', state=self.state2, region=self.region2, postcode="1234")

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

def createAdditionalEvents(self):
    self.previousYear = Year.objects.create(year=2019)
    self.previousYearEvent = Event.objects.create(
        year=self.previousYear,
        state=self.state1,
        name='Test event 1 2019',
        eventType='competition',
        status='published',
        maxMembersPerTeam=5,
        entryFeeIncludesGST=True,
        event_billingType='team',
        event_defaultEntryFee = 50,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-6)).date(),
        directEnquiriesTo = self.user1,
    )
    self.previousYearTeam = Team.objects.create(event=self.previousYearEvent, mentorUser=self.user1, name='Team 1', division=self.division1)

    self.newEvent = Event.objects.create(
        year=self.year,
        state=self.state1,
        name='Test event 2',
        eventType='competition',
        status='published',
        maxMembersPerTeam=3,
        entryFeeIncludesGST=True,
        event_billingType='team',
        event_defaultEntryFee = 50,
        startDate=(datetime.datetime.now() + datetime.timedelta(days=6)).date(),
        endDate = (datetime.datetime.now() + datetime.timedelta(days=6)).date(),
        registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-10)).date(),
        registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=1)).date(),
        directEnquiriesTo = self.user1,
    )
    self.newEventTeam = Team.objects.create(event=self.newEvent, mentorUser=self.user1, name='Team 2', division=self.division1)

class TestCopyTeamsList(TestCase):
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
        createAdditionalEvents(self)

    def testLoginRequired(self):
        url = reverse('teams:copyTeamsList', kwargs={'eventID': self.event.id})

        response = self.client.post(url, follow=True)
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/teams/copyExisting/{self.event.id}")
        self.assertEqual(response.status_code, 302)

    def testLoadsSuccess(self):
        url = reverse('teams:copyTeamsList', kwargs={'eventID': self.event.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def testDenied_notPublished(self):
        self.event.status = 'draft'
        self.event.save()
        url = reverse('teams:copyTeamsList', kwargs={'eventID': self.event.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Event is not published', status_code=403)

    def testDenied_registrationsClosed(self):
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
        self.event.save()
        url = reverse('teams:copyTeamsList', kwargs={'eventID': self.event.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Registration has closed for this event', status_code=403)

    def testDenied_workshop(self):
        self.event.eventType = 'workshop'
        self.event.save()
        url = reverse('teams:copyTeamsList', kwargs={'eventID': self.event.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Can only copy teams for competitions', status_code=403)

    def testContext_availableToCopyTeams_containsCorrectPreviousTeams_noSchoolSelected(self):
        url = reverse('teams:copyTeamsList', kwargs={'eventID': self.newEvent.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertIn(self.team1, response.context['availableToCopyTeams'])
        self.assertIn(self.team2, response.context['availableToCopyTeams'])
        self.assertNotIn(self.team3, response.context['availableToCopyTeams'])

    def testContext_availableToCopyTeams_containsCorrectPreviousTeams_schoolSelected(self):
        self.user1.currentlySelectedSchool = self.school1
        self.user1.save()
        url = reverse('teams:copyTeamsList', kwargs={'eventID': self.newEvent.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        response = self.client.get(url)
        self.assertNotIn(self.team1, response.context['availableToCopyTeams'])
        self.assertNotIn(self.team2, response.context['availableToCopyTeams'])
        self.assertIn(self.team3, response.context['availableToCopyTeams'])

    def testContext_availableToCopyTeams_containsCorrectPreviousTeams_wrongSchool(self):
        url = reverse('teams:copyTeamsList', kwargs={'eventID': self.newEvent.id})
        login = self.client.login(request=HttpRequest(), username=self.email2, password=self.password)

        response = self.client.get(url)
        self.assertNotIn(self.team1, response.context['availableToCopyTeams'])
        self.assertNotIn(self.team2, response.context['availableToCopyTeams'])
        self.assertNotIn(self.team3, response.context['availableToCopyTeams'])

    def testContext_availableToCopyTeams_currentEventTeamNotIn(self):
        url = reverse('teams:copyTeamsList', kwargs={'eventID': self.newEvent.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        response = self.client.get(url)
        self.assertNotIn(self.newEventTeam, response.context['availableToCopyTeams'])

    def testContext_availableToCopyTeams_previousYearEventTeamNotIn(self):
        url = reverse('teams:copyTeamsList', kwargs={'eventID': self.newEvent.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        response = self.client.get(url)
        self.assertNotIn(self.previousYearTeam, response.context['availableToCopyTeams'])

    def testContext_availableToCopyTeams_copiedTeamNotIn(self):
        self.newEventTeam1Copy = Team.objects.create(event=self.newEvent, mentorUser=self.user1, name='Team 1', division=self.division1, copiedFrom=self.team1)
        url = reverse('teams:copyTeamsList', kwargs={'eventID': self.newEvent.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        response = self.client.get(url)
        self.assertNotIn(self.team1, response.context['availableToCopyTeams'])

    def testContext_copiedTeams_uncopiedTeamNotIn(self):
        url = reverse('teams:copyTeamsList', kwargs={'eventID': self.newEvent.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        response = self.client.get(url)
        self.assertNotIn(self.team1, response.context['copiedTeams'])

    def testContext_copiedTeams_copiedTeamIn(self):
        self.newEventTeam1Copy = Team.objects.create(event=self.newEvent, mentorUser=self.user1, name='Team 1', division=self.division1, copiedFrom=self.team1)
        url = reverse('teams:copyTeamsList', kwargs={'eventID': self.newEvent.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)

        response = self.client.get(url)
        self.assertIn(self.team1, response.context['copiedTeams'])

class TestCopyTeam(TestCase):
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
        createAdditionalEvents(self)

    def testLoginRequired(self):
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})

        response = self.client.post(url, follow=True)
        self.assertContains(response, "Login")
    
        response = self.client.get(url)
        self.assertEqual(response.url, f"/accounts/login/?next=/teams/copyExisting/{self.newEvent.id}/create/{self.team1.id}")
        self.assertEqual(response.status_code, 302)

    def testDenied_notPublished(self):
        self.newEvent.status = 'draft'
        self.newEvent.save()
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Event is not published', status_code=403)

    def testDenied_registrationsClosed(self):
        self.newEvent.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
        self.newEvent.save()
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Registration has closed for this event', status_code=403)

    def testDenied_workshop(self):
        self.newEvent.eventType = 'workshop'
        self.newEvent.save()
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Can only copy teams for competitions', status_code=403)

    def testDenied_teamEventNotPublished(self):
        self.event.status = 'draft'
        self.event.save()
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Event for team is not published', status_code=403)

    def testDenied_noTeamPermission(self):
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email2, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'You are not an administrator of this team/ attendee', status_code=403)

    def testDenied_alreadyCopied(self):
        self.newEventTeam1Copy = Team.objects.create(event=self.newEvent, mentorUser=self.user1, name='Team 1', division=self.division1, copiedFrom=self.team1)
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Team already copied.', status_code=403)

    def testDenied_teamInEvent(self):
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.newEventTeam.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Team already in this event.', status_code=403)

    def testDenied_teamNotFromCurrentYear(self):
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.previousYearTeam.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Team not from current event year.', status_code=403)

    def testDenied_eventSchoolMaxReached(self):
        self.newEvent.event_maxTeamsPerSchool = 1
        self.newEvent.save()
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Max teams for school for this event reached. Contact the organiser if you want to register more teams for this event.', status_code=403)

    def testDenied_eventOverallMaxReached(self):
        self.newEvent.event_maxTeamsForEvent = 1
        self.newEvent.save()
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Max teams for this event reached. Contact the organiser if you want to register more teams for this event.', status_code=403)

    def testDenied_divisionNotAllowed(self):
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Division not allowed for this event.', status_code=403)

    def testDenied_eventSchoolMaxReached(self):
        self.newEventAvailableDivision1 = AvailableDivision.objects.create(event=self.newEvent, division=self.division1, division_maxTeamsPerSchool=1)
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Max teams for school for this event division reached. Contact the organiser if you want to register more teams in this division.', status_code=403)

    def testDenied_eventOverallMaxReached(self):
        self.newEventAvailableDivision1 = AvailableDivision.objects.create(event=self.newEvent, division=self.division1, division_maxTeamsForDivision=1)
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Max teams for this event division reached. Contact the organiser if you want to register more teams in this division.', status_code=403)

    def testDenied_existingName(self):
        self.newEventAvailableDivision1 = AvailableDivision.objects.create(event=self.newEvent, division=self.division1)
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team2.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Team with this name in this event already exists', status_code=403)

    def testDenied_numStudentsExceedsMax(self):
        self.newEventAvailableDivision1 = AvailableDivision.objects.create(event=self.newEvent, division=self.division1)
        for i in range(4):
            Student.objects.create(firstName=str(i), lastName=str(i), yearLevel=5, gender='other', team=self.team1)
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Number students in team exceeds limit for new event', status_code=403)

    def testSuccess_correctRedirect(self):
        self.newEventAvailableDivision1 = AvailableDivision.objects.create(event=self.newEvent, division=self.division1)
        for i in range(3):
            Student.objects.create(firstName=str(i), lastName=str(i), yearLevel=5, gender='other', team=self.team1)
        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/teams/copyExisting/{self.newEvent.id}")

    def testSuccess_oldTeamUnchanged(self):
        self.newEventAvailableDivision1 = AvailableDivision.objects.create(event=self.newEvent, division=self.division1)
        for i in range(3):
            Student.objects.create(firstName=str(i), lastName=str(i), yearLevel=5, gender='other', team=self.team1)
        updatedTime = self.team1.updatedDateTime
        numStudents = self.team1.student_set.count()

        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.team1.refresh_from_db()
        self.assertEqual(self.team1.updatedDateTime, updatedTime)
        self.assertEqual(self.team1.event, self.event)
        self.assertEqual(self.team1.student_set.count(), numStudents)

    def testSuccess_newTeamCreated(self):
        self.newEventAvailableDivision1 = AvailableDivision.objects.create(event=self.newEvent, division=self.division1)
        for i in range(3):
            Student.objects.create(firstName=str(i), lastName=str(i), yearLevel=5, gender='other', team=self.team1)
        self.assertEqual(Team.objects.filter(event=self.newEvent, name=self.team1.name).count(), 0)

        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(Team.objects.filter(event=self.newEvent, name=self.team1.name).count(), 1)

    def testSuccess_studentsCopied(self):
        self.newEventAvailableDivision1 = AvailableDivision.objects.create(event=self.newEvent, division=self.division1)
        for i in range(3):
            Student.objects.create(firstName=str(i), lastName=str(i), yearLevel=5, gender='other', team=self.team1)
        self.assertEqual(Student.objects.filter(team__event=self.newEvent, team__name=self.team1.name).count(), 0)

        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(Student.objects.filter(team__event=self.newEvent, team__name=self.team1.name).count(), 3)

    def testSuccess_copiedFromSet(self):
        self.newEventAvailableDivision1 = AvailableDivision.objects.create(event=self.newEvent, division=self.division1)
        for i in range(3):
            Student.objects.create(firstName=str(i), lastName=str(i), yearLevel=5, gender='other', team=self.team1)
        self.assertEqual(Team.objects.filter(copiedFrom=self.team1).count(), 0)

        url = reverse('teams:copyTeam', kwargs={'eventID': self.newEvent.id, 'teamID': self.team1.id})
        login = self.client.login(request=HttpRequest(), username=self.email1, password=self.password)
    
        response = self.client.get(url)
        self.assertEqual(Team.objects.filter(copiedFrom=self.team1).count(), 1)

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

    def testSave_NoSchool_NoExistingInvoice_freeEvent(self):
        self.event.event_defaultEntryFee = 0
        self.event.save()
        self.assertEqual(Invoice.objects.filter(event=self.event, invoiceToUser=self.user1, school=None).count(), 0)

        self.team1 = Team.objects.create(event=self.event, mentorUser=self.user1, name='Team 1', division=self.division1)
        self.assertEqual(Invoice.objects.filter(event=self.event, invoiceToUser=self.user1, school=None).count(), 0)

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

    def testHomeRegion_school(self):
        self.assertEqual(self.team3.homeRegion(), self.region2)

    def testHomeRegion_noSchool(self):
        self.assertEqual(self.team1.homeRegion(), self.region1)

    def testSchoolPostcode_school(self):
        self.assertEqual(self.team3.schoolPostcode(), "1234")

    def testSchoolPostcode_noSchool(self):
        self.assertEqual(self.team1.schoolPostcode(), None)

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
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "student_set-0-firstName": "First",
            "student_set-0-lastName": "Last",
            "student_set-0-yearLevel": 7,
            "student_set-0-gender": "male",
            "name":"Team 8",
            "division":self.division1.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Team.objects.filter(school=self.schoolAssertValue).count(), 2)

    def testInValidCreate_noStudents(self):
        self.assertEqual(self.user1.currentlySelectedSchool, self.schoolAssertValue)
        payload = {
            'student_set-TOTAL_FORMS':0,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "name":"Team 8",
            "division":self.division1.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please submit at least 1 form.")
        self.assertEqual(Team.objects.filter(school=self.schoolAssertValue).count(), 1)

    def testInValidCreate_schoolEventMax(self):
        self.assertEqual(self.user1.currentlySelectedSchool, self.schoolAssertValue)
        self.event.event_maxTeamsPerSchool = 1
        self.event.save()

        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "student_set-0-firstName": "First",
            "student_set-0-lastName": "Last",
            "student_set-0-yearLevel": 7,
            "student_set-0-gender": "male",
            "name":"Team 3",
            "division":self.division1.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Max teams for school for this event reached. Contact the organiser if you want to register more teams for this event.", status_code=403)
        self.assertEqual(Team.objects.filter(school=self.schoolAssertValue).count(), 1)
        self.assertEqual(Team.objects.filter(event=self.event).count(), 2)

    def testValidCreate_schoolEventMaxReached_redirectAddAnotherIgnored(self):
        self.assertEqual(self.user1.currentlySelectedSchool, self.schoolAssertValue)
        self.event.event_maxTeamsPerSchool = 2
        self.event.save()

        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "student_set-0-firstName": "First",
            "student_set-0-lastName": "Last",
            "student_set-0-yearLevel": 7,
            "student_set-0-gender": "male",
            "name":"Team 3",
            "division":self.division1.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'add_text': 'blah',
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/events/{self.event.id}")

    def testValidCreate_overallEventMaxReached_redirectAddAnotherIgnored(self):
        self.assertEqual(self.user1.currentlySelectedSchool, self.schoolAssertValue)
        self.event.event_maxTeamsForEvent = 3
        self.event.save()

        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "student_set-0-firstName": "First",
            "student_set-0-lastName": "Last",
            "student_set-0-yearLevel": 7,
            "student_set-0-gender": "male",
            "name":"Team 3",
            "division":self.division1.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
            'add_text': 'blah',
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/events/{self.event.id}")

    def testInValidCreate_overallEventMax(self):
        self.assertEqual(self.user1.currentlySelectedSchool, self.schoolAssertValue)
        self.event.event_maxTeamsForEvent = 2
        self.event.save()

        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "student_set-0-firstName": "First",
            "student_set-0-lastName": "Last",
            "student_set-0-yearLevel": 7,
            "student_set-0-gender": "male",
            "name":"Team 3",
            "division":self.division1.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Max teams for this event reached. Contact the organiser if you want to register more teams for this event.", status_code=403)
        self.assertEqual(Team.objects.filter(school=self.schoolAssertValue).count(), 1)
        self.assertEqual(Team.objects.filter(event=self.event).count(), 2)

    def testInValidCreate_schoolDivisionMax(self):
        self.assertEqual(self.user1.currentlySelectedSchool, self.schoolAssertValue)
        self.availableDivision.division_maxTeamsPerSchool = 1
        self.availableDivision.save()

        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "student_set-0-firstName": "First",
            "student_set-0-lastName": "Last",
            "student_set-0-yearLevel": 7,
            "student_set-0-gender": "male",
            "name":"Team 3",
            "division":self.division1.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Division: Select a valid choice. That choice is not one of the available choices.")
        self.assertContains(response, "Division 1: Max teams for school for this event division reached. Contact the organiser if you want to register more teams in this division.")
        self.assertEqual(Team.objects.filter(school=self.schoolAssertValue).count(), 1)
        self.assertEqual(Team.objects.filter(event=self.event).count(), 2)

    def testGet_schoolDivisionMax(self):
        self.availableDivision.division_maxTeamsPerSchool = 1
        self.availableDivision.save()

        response = self.client.get(reverse('teams:create', kwargs={'eventID':self.event.id}), follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Division 1: Max teams for school for this event division reached. Contact the organiser if you want to register more teams in this division.")

    def testInValidCreate_overallDivisionMax(self):
        self.assertEqual(self.user1.currentlySelectedSchool, self.schoolAssertValue)
        self.availableDivision.division_maxTeamsForDivision = 2
        self.availableDivision.save()

        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "student_set-0-firstName": "First",
            "student_set-0-lastName": "Last",
            "student_set-0-yearLevel": 7,
            "student_set-0-gender": "male",
            "name":"Team 3",
            "division":self.division1.id,
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Division: Select a valid choice. That choice is not one of the available choices.")
        self.assertContains(response, "Division 1: Max teams for this event division reached. Contact the organiser if you want to register more teams in this division.")
        self.assertEqual(Team.objects.filter(school=self.schoolAssertValue).count(), 1)
        self.assertEqual(Team.objects.filter(event=self.event).count(), 2)

    def testGet_overallDivisionMax(self):
        self.availableDivision.division_maxTeamsForDivision = 2
        self.availableDivision.save()

        response = self.client.get(reverse('teams:create', kwargs={'eventID':self.event.id}), follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Division 1: Max teams for this event division reached. Contact the organiser if you want to register more teams in this division.")

    def testInValidCreate_division(self):
        self.assertEqual(self.user1.currentlySelectedSchool, self.schoolAssertValue)
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "student_set-0-firstName": "First",
            "student_set-0-lastName": "Last",
            "student_set-0-yearLevel": 7,
            "student_set-0-gender": "male",
            "name":"Team 3",
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
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":1,
            "student_set-MAX_NUM_FORMS":self.event.maxMembersPerTeam,
            "student_set-0-firstName": "First",
            "student_set-0-lastName": "Last",
            "student_set-0-yearLevel": 7,
            "student_set-0-gender": "male",
            "name":"Team 3",
            'hardwarePlatform': self.hardware.id,
            'softwarePlatform': self.software.id,
        }
        response = self.client.post(reverse('teams:create', kwargs={'eventID':self.event.id}), data=payload, follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
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

# Unit tests

# Forms

class TestTeamForm(TestCase):
    email1 = 'user1@user.com'
    email2 = 'user2@user.com'
    email3 = 'user3@user.com'
    email_superUser = 'user4@user.com'
    password = 'chdj48958DJFHJGKDFNM'

    def setUp(self):
        newCommonSetUp(self)
        self.availableDivision = AvailableDivision.objects.create(division=self.division1, event=self.event)
        self.hardwarePlatform = HardwarePlatform.objects.create(name='H1')
        self.softwarePlatform = SoftwarePlatform.objects.create(name='H1')

    def createForm(self, data):
        return TeamForm(data=data, event=self.event, user=self.user1)

    def testFieldsRequired(self):
        form = self.createForm({})

        self.assertEqual(form.is_valid(), False)
        self.assertEqual(form.errors["division"], ["This field is required."])
        self.assertEqual(form.errors["name"], ["This field is required."])
        self.assertEqual(form.errors["hardwarePlatform"], ["This field is required."])
        self.assertEqual(form.errors["softwarePlatform"], ["This field is required."])

    def testValidForm(self):
        form = self.createForm({
            'division': self.division1.id,
            'name': 'A team name',
            'hardwarePlatform': self.hardwarePlatform.id,
            'softwarePlatform': self.softwarePlatform.id,
        })

        self.assertTrue(form.is_valid())

    def testInvalidForm_division(self):
        form = self.createForm({
            'division': self.division2.id,
            'name': 'A team name',
            'hardwarePlatform': self.hardwarePlatform.id,
            'softwarePlatform': self.softwarePlatform.id,
        })

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["division"], ["Select a valid choice. That choice is not one of the available choices."])

    def testInvalidForm_divisionMaxReached(self):
        self.availableDivision.division_maxTeamsForDivision = 0
        self.availableDivision.save()

        form = self.createForm({
            'division': self.division1.id,
            'name': 'A team name',
            'hardwarePlatform': self.hardwarePlatform.id,
            'softwarePlatform': self.softwarePlatform.id,
        })

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["division"], ["Select a valid choice. That choice is not one of the available choices."])
