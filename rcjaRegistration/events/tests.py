from django.test import TestCase
from regions.models import State,Region
from schools.models import School, SchoolAdministrator
from teams.models import Team,Student
from events.models import Event,Division,Year
from users.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.http import HttpRequest

import datetime
# Create your tests here.


def commonSetUp(obj):
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
    obj.oldeventTeam = Team.objects.create(event=obj.oldEventWithTeams, division=obj.division, school=obj.newSchool, mentorUser=obj.user, name='test')
    obj.oldTeamStudent = Student(team=obj.oldeventTeam,firstName='test',lastName='old',yearLevel=1,gender='Male',birthday=datetime.datetime.now().date())
    
    obj.newEventTeam = Team.objects.create(event=obj.newEvent, division=obj.division, school=obj.newSchool, mentorUser=obj.user, name='test new team')
    obj.newTeamStudent = Student(team=obj.newEventTeam,firstName='test',lastName='new',yearLevel=1,gender='Male',birthday=datetime.datetime.now().date())

    login = obj.client.login(request=HttpRequest(), username=obj.username, password=obj.password) 

class TestIndexDashboard(TestCase): #TODO more comprehensive tests
    
    def setUp(self):
        commonSetUp(self)
        
    
    def testPageLoad(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertEqual(200, response.status_code)    
    def testNonSignedUpOldDoesNotLoad(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertNotIn(b'test old not reg',response.content)
    def testNewEventWithRegoLoads(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertIn(b'test new not reg',response.content)
    def testOldEventWithTeamsLoad(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertIn(b'test old yes reg',response.content)

    def testEventsAreSorted(self):
        pass
    def testEventDetailsLoad(self):
        pass

class TestEventSummaryPage(TestCase):
    def setUp(self):
        commonSetUp(self)
    def testPageLoad(self):
        response = self.client.get(reverse('events:summary', kwargs= {'eventID':self.oldEvent.id}))        
        self.assertEqual(200, response.status_code) 
    def testTeamsLoad(self):
        response = self.client.get(reverse('events:summary', kwargs= {'eventID':self.oldEvent.id}))        
        self.assertIn(b'test old',response.content)
    def testOldEventNotRegisterable(self):
        response = self.client.get(reverse('events:summary', kwargs= {'eventID':self.oldEvent.id}))
        self.assertContains(response,'Registration for this event has closed.')
        #print(response.content)
        #self.assert(response,'edit')
    def testCreationButtonsVisibleWhenRegoOpen(self):
        response = self.client.get(reverse('events:summary', kwargs= {'eventID':self.newEvent.id}))
        self.assertNotContains(response,'Registration for this event has closed.')

class TestEventClean(TestCase):
    def setUp(self):
        commonSetUp(self)
        self.event = Event(
            year=self.year,
            state=self.newState,
            name='test old not reg',
            maxMembersPerTeam=5,
            event_defaultEntryFee = 4,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            directEnquiriesTo = self.user     
        )
    
    def testMultidayEventOK(self):
        self.event.clean()

    def testSingleDayEventOK(self):
        self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+5)).date()
        self.event.clean()

    def testStartBeforeEnd(self):
        try:
            self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+4)).date()
            self.event.clean()
        except ValidationError:
            pass
        else:
            raise ValidationError('Date verification failed')

    def testRegistrationOpenBeforeClose(self):
        try:
            self.event.startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date()
            self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date()
            self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
            self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-4)).date()
            self.event.clean()
        except ValidationError:
            pass
        else:
            raise ValidationError('Date verification failed')

    def testOneDayRegistration(self):
        self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
        self.event.clean()

    def testRegistrationCloseOnEventStartDate(self):
        try:
            self.event.startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date()
            self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date()
            self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
            self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+5)).date()
            self.event.clean()
        except ValidationError:
            pass
        else:
            raise ValidationError('Date verification failed')

    def testRegistrationCloseAfterEventStartDate(self):
        try:
            self.event.startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date()
            self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date()
            self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
            self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date()
            self.event.clean()
        except ValidationError:
            pass
        else:
            raise ValidationError('Date verification failed')
