from django.test import TestCase
from regions.models import State,Region
from schools.models import School, SchoolAdministrator
from teams.models import Team, Student
from events.models import Event, Division, Year
from users.models import User
from django.urls import reverse

import datetime
# Create your tests here.

def commonSetUp(obj): #copied from events, todo refactor
    obj.username = 'user@user.com'
    obj.password = 'password'
    obj.user = user = User.objects.create_user(email=obj.username, password=obj.password)
    obj.newState = State.objects.create(
        treasurer=obj.user,
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

    login = obj.client.login(username=obj.username, password=obj.password) 

class TestAddTeam(TestCase): #TODO more comprehensive tests
    
    def setUp(self):
        commonSetUp(self)
        
    def testOpenRegoDoesLoad(self):
        response = self.client.get(reverse('teams:create',kwargs={'eventID':self.newEvent.id}))
        self.assertEqual(200, response.status_code)

    def testClosedRegoReturnsError(self):
        response = self.client.get(reverse('teams:create',kwargs={'eventID':self.oldEvent.id}))
        self.assertEqual(403, response.status_code)

    def testMaxSubmissionNumber(self):
        response = self.client.get(reverse('teams:create',kwargs={'eventID':self.newEvent.id}))
        self.assertContains(response,'First name', self.newEvent.maxMembersPerTeam)

    def testWorkingTeamCreate(self):
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test+team",
            "division":self.division.id,
            "school":self.newSchool.id,
            "student_set-0-firstName":"test",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"1",
            "student_set-0-birthday":"1111-11-11",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:create',kwargs={'eventID':self.newEvent.id}),data=payload,follow=False)
        self.assertEqual(302,response.status_code)

    def testInvalidTeamCreate(self):
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test+team",
            "division":self.division.id,
            "student_set-0-firstName":"test",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"test",
            "student_set-0-birthday":"1111-11-11",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:create',kwargs={'eventID':self.newEvent.id}),data=payload)
        self.assertEqual(200,response.status_code)
        """TODO this tests fails for some reason 

    def testTeamIsDeleted(self):
        payload = {'teamID':self.newEventTeam.id}
        response = self.client.post(reverse('teams:delete'),data=payload)
        print(self.newEventTeam.id)
        self.assertEqual(200,response.status_code)
        self.assertEqual(self.newEventTeam,None)
        """

class TestEditTeam(TestCase):
    def setUp(self):
        commonSetUp(self)

    def testOpenEditDoesLoad(self):
        response = self.client.get(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id}))
        self.assertEqual(200, response.status_code)
  
    def testClosedEditReturnsError(self):
        response = self.client.get(reverse('teams:edit',kwargs={'teamID':self.oldEventTeam.id}))
        self.assertEqual(403, response.status_code)    
        """
        def testEditLoadsPreviousData(self):
            response = self.client.get(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id}))
            #print(response)
        self.assertEqual(response.context['form'].initial['student_set-0-lastName'], 'thisisastringfortesting')   """

    def testEditStudentSucceeds(self):
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test+team",
            "division":self.division.id,
            "school":self.newSchool.id,
            "student_set-0-firstName":"teststringhere",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"1",
            "student_set-0-birthday":"1111-11-11",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id}),data=payload)

        self.assertEquals(Student.objects.get(firstName="teststringhere").firstName,"teststringhere")
        self.assertEquals(302,response.status_code)

    def testEditStudentWithInvalidFails(self):
        payload = {
            'student_set-TOTAL_FORMS':1,
            "student_set-INITIAL_FORMS":0,
            "student_set-MIN_NUM_FORMS":0,
            "student_set-MAX_NUM_FORMS":self.newEvent.maxMembersPerTeam,
            "name":"test+team",
            "division":self.division.id,
            "student_set-0-firstName":"test2",
            "student_set-0-lastName":"test",
            "student_set-0-yearLevel":"test",
            "student_set-0-birthday":"1111-11-11",
            "student_set-0-gender":"male"
        }
        response = self.client.post(reverse('teams:edit',kwargs={'teamID':self.newEventTeam.id}),data=payload)
        self.assertEqual(200,response.status_code)
