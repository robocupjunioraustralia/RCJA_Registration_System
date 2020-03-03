from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.http import HttpRequest

from regions.models import State,Region
from schools.models import School, SchoolAdministrator
from teams.models import Team, Student
from events.models import Event, Division, Year, AvailableDivision
from users.models import User

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
        self.assertEqual(response.status_code, 200)

    def testNonSignedUpOldDoesNotLoad(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertNotContains(response, 'test old not reg')

    def testNewEventWithRegoLoads(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertContains(response, 'test new not reg')

    def testOldEventWithTeamsLoad(self):
        response = self.client.get(reverse('events:dashboard'))
        self.assertContains(response, 'test old yes reg')

    def testEventsAreSorted(self):
        pass

    def testEventDetailsLoad(self):
        pass

class TestEventSummaryPage(TestCase):
    def setUp(self):
        commonSetUp(self)

    def testPageLoad(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.oldEvent.id}))
        self.assertEqual(response.status_code, 200)

    def testTeamsLoad(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.oldEvent.id}))
        self.assertContains(response, 'test old')

    def testOldEventNotRegisterable(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.oldEvent.id}))
        self.assertContains(response,'Registration for this event has closed.')
        #print(response.content)
        #self.assert(response,'edit')

    def testCreationButtonsVisibleWhenRegoOpen(self):
        response = self.client.get(reverse('events:details', kwargs= {'eventID':self.newEvent.id}))
        self.assertNotContains(response,'Registration for this event has closed.')

class TestEventClean(TestCase):
    def setUp(self):
        commonSetUp(self)
        self.division1 = Division.objects.create(name='Division 1')
        self.event = Event(
            year=self.year,
            state=self.newState,
            name='Event 1',
            maxMembersPerTeam=5,
            event_defaultEntryFee = 4,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            directEnquiriesTo = self.user     
        )

    # Dates validation

    def teststartDateNoneInvalid(self):
        self.event.startDate = None
        self.assertRaises(ValidationError, self.event.clean)

    def testendDateNoneInvalid(self):
        self.event.endDate = None
        self.assertRaises(ValidationError, self.event.clean)

    def testRegistrationsOpenDateNoneInvalid(self):
        self.event.registrationsOpenDate = None
        self.assertRaises(ValidationError, self.event.clean)

    def testRegistrationsCloseDateNoneInvalid(self):
        self.event.registrationsCloseDate = None
        self.assertRaises(ValidationError, self.event.clean)

    def testMultidayEventOK(self):
        self.event.clean()

    def testSingleDayEventOK(self):
        self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+5)).date()
        self.event.clean()

    def testStartBeforeEnd(self):
        self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+4)).date()
        self.assertRaises(ValidationError, self.event.clean)

    def testRegistrationOpenBeforeClose(self):
        self.event.startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date()
        self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date()
        self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-4)).date()
        self.assertRaises(ValidationError, self.event.clean)

    def testOneDayRegistration(self):
        self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
        self.event.clean()

    def testRegistrationCloseOnEventStartDate(self):
        self.event.startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date()
        self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date()
        self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+5)).date()
        self.assertRaises(ValidationError, self.event.clean)

    def testRegistrationCloseAfterEventStartDate(self):
        self.event.startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date()
        self.event.endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date()
        self.event.registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-3)).date()
        self.event.registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date()
        self.assertRaises(ValidationError, self.event.clean)

    # Billing settings validation

    def testSpecialRateValidComplete(self):
        self.event.event_specialRateFee = 50
        self.event.event_specialRateNumber = 5
        self.event.clean()

    def testSpecialRateInvalid(self):
        self.event.event_specialRateFee = 50
        self.assertRaises(ValidationError, self.event.clean)

    def testSpecialRateStudentInvalid(self):
        self.event.event_specialRateFee = 50
        self.event.event_specialRateNumber = 5
        self.event.clean()

        self.event.event_billingType = 'student'
        self.assertRaises(ValidationError, self.event.clean)
    
    def testSpecialRateBillingAvailableDivisionValid(self):
        self.event.save()
        self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division1)
        self.event.event_specialRateFee = 50
        self.event.event_specialRateNumber = 5
        self.event.clean()

    def testSpecialRateBillingAvailableDivisionInValid(self):
        self.event.save()
        self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division1)
        self.event.event_specialRateFee = 50
        self.event.event_specialRateNumber = 5
        self.event.clean()

        self.availableDivision.division_billingType = 'team'
        self.availableDivision.division_entryFee = 50
        self.availableDivision.save()

        self.assertRaises(ValidationError, self.event.clean)

class TestEventMethods(TestCase):
    def setUp(self):
        commonSetUp(self)
        self.division1 = Division.objects.create(name='Division 1')
        self.event = Event(
            year=self.year,
            state=self.newState,
            name='Event 1',
            maxMembersPerTeam=5,
            event_defaultEntryFee = 4,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            directEnquiriesTo = self.user     
        )

    def testGetState(self):
        self.assertEqual(self.event.getState(), self.newState)

    def testBoolWorkshop_notWorkshop(self):
        self.event.eventType = 'competition'
        self.assertEqual(self.event.boolWorkshop(), False)

    def testBoolWorkshop_isWorkshop(self):
        self.event.eventType = 'workshop'
        self.assertEqual(self.event.boolWorkshop(), True)

    def testSave_competition(self):
        self.event.eventType = 'competition'
        self.event.event_billingType = 'student'
        self.assertEqual(self.event.maxMembersPerTeam, 5)
        self.assertEqual(self.event.event_billingType, 'student')

        self.event.save()
        self.assertEqual(self.event.maxMembersPerTeam, 5)
        self.assertEqual(self.event.event_billingType, 'student')

    def testSave_workshop(self):
        self.event.eventType = 'workshop'
        self.event.event_billingType = 'student'
        self.assertEqual(self.event.maxMembersPerTeam, 5)
        self.assertEqual(self.event.event_billingType, 'student')

        self.event.save()
        self.assertEqual(self.event.maxMembersPerTeam, 0)
        self.assertEqual(self.event.event_billingType, 'team')

    def testStr_state(self):
        self.assertEqual(str(self.event), "Event 1 2019 (VIC)")

    def testStr_global(self):
        self.event.globalEvent = True
        self.assertEqual(str(self.event), "Event 1 2019")

class TestAvailableDivisionClean(TestCase):
    def setUp(self):
        commonSetUp(self)
        self.division1 = Division.objects.create(name='Division 1')
        self.event = Event(
            year=self.year,
            state=self.newState,
            name='Event 1',
            maxMembersPerTeam=5,
            event_defaultEntryFee = 4,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            directEnquiriesTo = self.user     
        )
        self.event.save()
        self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division1)

    def testBillingEntryFeeAndTypeValidBlank(self):
        self.availableDivision.clean()

    def testBillingEntryFeeAndTypeValidFilled(self):
        self.availableDivision.division_billingType = 'team'
        self.availableDivision.division_entryFee = 50
        self.availableDivision.clean()

    def testBillingEntryFeeAndTypeInValid1(self):
        self.availableDivision.division_billingType = 'team'
        self.assertRaises(ValidationError, self.availableDivision.clean)

    def testBillingEntryFeeAndTypeInValid2(self):
        self.availableDivision.division_entryFee = 50
        self.assertRaises(ValidationError, self.availableDivision.clean)

    def testSpecialRateValid(self):
        self.event.event_specialRateFee = 50
        self.event.event_specialRateNumber = 5
        self.event.save()

        self.availableDivision.clean()

    def testSpecialRateInValid(self):
        self.event.event_specialRateFee = 50
        self.event.event_specialRateNumber = 5
        self.event.save()

        self.availableDivision.division_billingType = 'team'
        self.assertRaises(ValidationError, self.availableDivision.clean)

        self.availableDivision.division_billingType = 'student'
        self.assertRaises(ValidationError, self.availableDivision.clean)

    def testWorkshopValid(self):
        self.event.eventType = 'workshop'
        self.event.save()

        self.availableDivision.clean()

        self.availableDivision.division_billingType = 'team'
        self.availableDivision.division_entryFee = 50
        self.availableDivision.clean()

    def testWorkshopInValid(self):
        self.event.eventType = 'workshop'
        self.event.save()

        self.availableDivision.division_billingType = 'student'
        self.availableDivision.division_entryFee = 50
        self.assertRaises(ValidationError, self.availableDivision.clean)

class TestAvailableDivisionMethods(TestCase):
    def setUp(self):
        commonSetUp(self)
        self.division1 = Division.objects.create(name='Division 1')
        self.event = Event(
            year=self.year,
            state=self.newState,
            name='Event 1',
            maxMembersPerTeam=5,
            event_defaultEntryFee = 4,
            startDate=(datetime.datetime.now() + datetime.timedelta(days=+5)).date(),
            endDate = (datetime.datetime.now() + datetime.timedelta(days=+6)).date(),
            registrationsOpenDate = (datetime.datetime.now() + datetime.timedelta(days=-5)).date(),
            registrationsCloseDate = (datetime.datetime.now() + datetime.timedelta(days=-1)).date(),
            directEnquiriesTo = self.user     
        )
        self.event.save()
        self.availableDivision = AvailableDivision.objects.create(event=self.event, division=self.division1)

    def testGetState(self):
        self.assertEqual(self.availableDivision.getState(), self.newState)
